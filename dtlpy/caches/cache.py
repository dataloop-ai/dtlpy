import json
import os
import shutil
import time
from enum import Enum
from pathlib import Path
import mmap
from filelock import FileLock
import logging
import base64

from .dl_cache import DiskCache
from .redis_cache import RedisCache
from .filesystem_cache import FileSystemCache

logger = logging.getLogger(name='dtlpy')


class ObjectType(str, Enum):
    BINARY = "binary"
    OBJECT = "object"


class CacheType(Enum):
    DISKCACHE = 'diskcache'
    REDIS = 'redis'
    FILESYSTEM = 'filesystem'


class CacheConfig:
    def __init__(self, cache_type=CacheType.DISKCACHE, ttl=1000, level=1, options=None):
        """
        Cache config settings

        :param CacheType cache_type: CacheType diskcache, filesystem, redis
        :param int ttl: time to hold the item in the cache in seconds (SEC)
        :param int level: cache level
        :param dict options: the configs for the caches types
        """
        if isinstance(cache_type, CacheType):
            cache_type = cache_type.value
        if isinstance(cache_type, str) and cache_type not in CacheType._value2member_map_:
            raise ValueError('cache type must be redis or diskcache')

        self.type = cache_type
        self.ttl = ttl
        self.level = level
        self.options = options

    def to_string(self):
        """
        convert object to base 64 string
        """
        base64_bytes = base64.b64encode(json.dumps(self.to_json()).encode("ascii"))
        base64_string = base64_bytes.decode("ascii")
        return base64_string

    @staticmethod
    def from_string(cls, base64_string):
        """
        convert from base 64 string to the class object

        :param str base64_string: string in base64 the have a json configs
        """
        base64_bytes = base64_string.encode("ascii")
        sample_string_bytes = base64.b64decode(base64_bytes)
        _json = json.loads(sample_string_bytes.decode("ascii"))
        return cls(cache_type=_json.get('type', CacheType.DISKCACHE),
                   ttl=_json.get('ttl', 1000),
                   level=_json.get('level', 1),
                   options=_json.get('options', None))

    def to_json(self):
        """
        convert the class to json
        """
        return {
            'type': self.type,
            'ttl': self.ttl,
            'level': self.level,
            'options': self.options,
        }

    @staticmethod
    def from_json(cls, _json):
        """
        make a class attribute from json

        :param _json: _json have the class attributes
        """
        if isinstance(_json, str):
            _json = json.loads(_json)
        return cls(cache_type=_json.get('type', CacheType.DISKCACHE),
                   ttl=_json.get('ttl', 1000),
                   level=_json.get('level', 1),
                   options=_json.get('options', None))


class CacheKey:
    def __init__(self,
                 master_type='**',
                 master_id='**',
                 entity_type='**',
                 entity_id='*',
                 object_type=ObjectType.OBJECT):
        """
        :param str master_type: master type
        :param str master_id: master id
        :param str entity_type: entity type
        :param str entity_id: entity id
        :param str object_type: object type object/binary
        """
        self.master_type = master_type
        self.master_id = master_id
        self.entity_type = entity_type
        self.entity_id = entity_id
        self.object_type = object_type

    def get(self):
        """
        return the build key
        """
        return os.path.join(self.master_type, self.master_id, self.entity_type, self.entity_id, self.object_type)

    def get_key(self):
        """
        return the build key
        """
        return os.path.join(self.entity_type, self.entity_id, self.object_type)


class CacheManger:
    def __init__(self, cache_configs: list, bin_cache_size=1000):
        """
        Cache manger for config and mange the cache

        :param cache_configs: CacheConfig object
        :param bin_cache_size: size on MB for binary cache
        """
        self.cache_levels = dict()
        self._max_level = 1
        self.bin_cache_size = bin_cache_size
        self.bin_cache_path = os.environ['DEFAULT_CACHE_PATH_BIN']
        self._current_bin_cache_size = 0
        for config in cache_configs:
            try:
                self.cache_levels[config.level] = self._load_cache_handler(config)
                if config.level < self._max_level:
                    self._max_level = config.level
            except:
                raise "Failed to build Cache"

        self.parent_dict = {
            "annotations": 'items',
            "items": 'datasets',
            "datasets": 'projects',
            "projects": 'org',
            "org": '',
            "annotationtasks": 'datasets',
            "assignments": 'annotationtasks',
            "snapshots": 'models',
            "packages": 'projects',
            "services": 'packages',
        }

    def _load_cache_handler(self, config: CacheConfig):
        """
        the function the build the cache form the configs that get
        """
        from ..services import DataloopLogger
        cache = None
        if config.type == CacheType.REDIS.value:
            try:
                cache = RedisCache(options=config.options, ttl=config.ttl)
            except:
                logger.warning("Failed to build Redis")
                raise Exception("Failed to build Redis")

        elif config.type == CacheType.DISKCACHE.value:
            cache = DiskCache(name='object_cache', options=config.options, ttl=config.ttl)
        elif config.type == CacheType.FILESYSTEM.value:
            cache = FileSystemCache(options=config.options, ttl=config.ttl)
            DataloopLogger.clean_dataloop_cache(cache_path=cache.root_dir,
                                                max_param={'max_time': cache.ttl})
        DataloopLogger.clean_dataloop_cache(cache_path=self.bin_cache_path,
                                            max_param={'max_time': config.ttl})
        return cache

    def get(self, key: CacheKey):
        """
        Cache get

        :param CacheKey key: CacheKey object
        :return: success, list of the get result
        """
        res = []
        success = False
        for i in range(1, self._max_level + 1):
            res = self.cache_levels[i].get(key=key.get_key())
            if res:
                success = True
                break
        return success, res

    def set(self, key: str, value):
        """
        Cache set, add or update the key value

        :param CacheKey key: CacheKey object
        :param value: value to set
        """
        if isinstance(value, dict):
            value = json.dumps(value)
        self.cache_levels[1].set(key, value)

    def _delete_parent(self, key: CacheKey, level):
        parent_key = CacheKey(master_type=self.parent_dict[key.entity_type],
                              entity_type=key.entity_type,
                              entity_id=key.entity_id,
                              object_type='*')
        list_keys = self.cache_levels[level].list(pattern=parent_key.get())
        for k in list_keys:
            if 'binary' in k:
                val = self.cache_levels[level].get(key=k)
                if os.path.isfile(val):
                    os.remove(val)
            self.cache_levels[level].delete(k)

    def delete(self, key: CacheKey):
        """
        Cache delete

        :param CacheKey key: CacheKey object
        """
        for i in range(1, self._max_level + 1):
            self.cache_levels[i].delete(key.get_key())
            self._delete_parent(key=key, level=i)
            key.object_type = '*'
            list_keys = self.cache_levels[i].list(pattern=key.get_key())
            for k in list_keys:
                val = self.cache_levels[i].get(key=k)
                self.cache_levels[i].delete(k)
                if 'binary' in k:
                    if os.path.isfile(val):
                        os.remove(val)
                    continue
                e_type, e_id, e_obj = val.split('\\')
                self.delete(key=CacheKey(entity_type=e_type, entity_id=e_id, object_type=e_obj))

    def build_cache_key(self, entity_json: dict):
        """
        Build a format of the cache key from the entity json we get

        :param dict entity_json: json of an entity
        :return: CacheKey object
        """
        child_entity = False
        if 'url' in entity_json:
            split_url = entity_json['url'].split('/')
            entity_type = split_url[-2]
            child_entity = True
        elif 'org' in entity_json:
            entity_type = 'projects'
        else:
            entity_type = 'org'
        entity_id = entity_json['id']
        master_type = self.parent_dict[entity_type]
        master_id = '**'
        if child_entity:
            master_id_key = master_type[:-1] + 'Id'
            if master_id_key in entity_json:
                master_id = entity_json[master_id_key]
            elif master_type in entity_json:
                master_id = entity_json[master_type][0]
        elif entity_type == 'projects':
            master_id = entity_json[master_type]['id']

        return CacheKey(master_type=master_type, master_id=master_id, entity_type=entity_type, entity_id=entity_id)

    def _update_config_file(self, filepath: str, update: bool, size: float = 0):
        """
        Update the config file the have all the details about binary cache

        :param str filepath: path of the file the work on
        :param bool update: if True update the use of the file
        :param int size: file size
        """
        config_file_path = os.path.join(self.bin_cache_path, 'cacheConfig.json')
        if os.path.isfile(config_file_path):
            with FileLock(config_file_path + ".lock"):
                with open(config_file_path, mode="r", encoding="utf-8") as con:
                    with mmap.mmap(con.fileno(), length=0, access=mmap.ACCESS_READ) as mmap_obj:
                        text = mmap_obj.read().decode('utf8').replace("'", '"')
                        config_file = json.loads(text)
        else:
            config_file = {'size': 0, 'keys': []}

        if update and filepath in config_file['keys']:
            config_file['keys'].remove(filepath)

        if filepath not in config_file['keys']:
            config_file['keys'].append(filepath)
        config_file['size'] += size
        self._current_bin_cache_size = config_file['size']
        json_object = json.dumps(config_file, indent=4)
        with FileLock(config_file_path + ".lock"):
            with open(config_file_path, mode="w", encoding="utf-8") as outfile:
                outfile.write(json_object)

    def _lru_cache(self):
        """
        Make lru on the binary cache remove 30% of the files
        """
        config_file_path = os.path.join(self.bin_cache_path, 'cacheConfig.json')
        with FileLock(config_file_path + ".lock"):
            with open(config_file_path, mode="r", encoding="utf-8") as con:
                with mmap.mmap(con.fileno(), length=0, access=mmap.ACCESS_READ) as mmap_obj:
                    text = mmap_obj.read().decode('utf8').replace("'", '"')
                    config_file = json.loads(text)

        size = config_file['size']
        end = 70 / 100 * self.bin_cache_size

        while size > end and len(config_file['keys']) > 1:
            to_delete = config_file['keys'][0]

            size -= (Path(to_delete).stat().st_size / 1000000)
            os.remove(to_delete)
            config_file['keys'].remove(to_delete)

        config_file['size'] = size
        json_object = json.dumps(config_file, indent=4)

        with FileLock(config_file_path + ".lock"):
            with open(config_file_path, "w") as outfile:
                outfile.write(json_object)

    def read_stream(self, request_path, dataset_id=None):
        """
        Cache binary get

        :param str request_path: the request
        :param str dataset_id: dataset id of the binary object
        :return: success, list of the get result
        """
        entity_id = request_path.split('/')[-2]
        key = CacheKey(master_type='datasets',
                       master_id=dataset_id,
                       entity_id=entity_id,
                       entity_type='items',
                       object_type=ObjectType.BINARY.value)
        hit, response = self.get(key=key)
        if hit:
            source_path = os.path.normpath(response[0])
            self._update_config_file(filepath=source_path, update=True)
            return hit, [source_path]
        else:
            return False, None

    def write_stream(self,
                     request_path,
                     response=None,
                     buffer=None,
                     file_name=None,
                     entity_id=None,
                     dataset_id=None
                     ):
        """
        Cache binary set

        :param  request_path: the request
        :param  response: the response of stream
        :param  buffer: the steam buffer
        :param  file_name: the file name
        :param  entity_id: entity id
        :param  dataset_id: dataset id of the binary object
        :return: the file path of the binary
        """
        if entity_id is None:
            entity_id = request_path.split('/')[-2]
        key = CacheKey(master_type='datasets',
                       master_id=dataset_id,
                       entity_id=entity_id,
                       entity_type='items',
                       object_type=ObjectType.BINARY)
        filepath = self.bin_cache_path
        if file_name is None:
            file_name = (dict(response.headers)['Content-Disposition'].split('=')[1][2:-1])
        filepath = os.path.join(
            filepath,
            'items',
            file_name
        )
        self.set(key=key.get(), value=filepath)
        if not os.path.isfile(filepath):
            os.makedirs(os.path.dirname(filepath), exist_ok=True)
            if buffer is None:
                try:
                    with open(filepath, "wb") as f:
                        for chunk in response.iter_content(chunk_size=8192):
                            if chunk:  # filter out keep-alive new chunks
                                f.write(chunk)
                except:
                    if os.path.isfile(filepath):
                        os.remove(filepath)
                    return ''
            else:
                shutil.copyfile(buffer.name, filepath)
        self._update_config_file(filepath=filepath, update=False, size=(Path(filepath).stat().st_size / 1000000))
        if (Path(filepath).stat().st_size / 1000000) + self._current_bin_cache_size > self.bin_cache_size:
            self._lru_cache()
        return filepath

    def read(self, request_path: str):
        """
        Cache entity get

        :param str request_path: the request
        :return: success, list of the get result
        """
        entity_id = request_path.split('/')[-1]
        entity_type = request_path.split('/')[-2]
        key = CacheKey(entity_id=entity_id, entity_type=entity_type)
        hit, response = self.get(key=key)
        if hit:
            return hit, response
        return False, None

    def write(self, list_entities_json):
        """
        Add or update the entity cache

        :param list list_entities_json: list of jsons of entities to set
        """
        for entity_json in list_entities_json:
            key = self.build_cache_key(entity_json)
            redis_key = key.get_key()
            self.set(key=redis_key, value=entity_json)
            self.set(key=key.get(), value=redis_key)

    def invalidate(self, path):
        """
        Delete from the caches

        :param str path: the request path
        """
        entity_id = path.split('/')[-1]
        entity_type = path.split('/')[-2]
        key = CacheKey(entity_id=entity_id, entity_type=entity_type)
        self.delete(key)

    def clear(self):
        self.cache_levels[1].clear()

    def keys(self):
        return [k for k in self.cache_levels[1].keys()]
