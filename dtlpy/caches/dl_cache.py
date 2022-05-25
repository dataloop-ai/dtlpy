import json
import sqlite3
import re

from diskcache import Cache
import os
from .base_cache import BaseCache


class DiskCache(BaseCache):
    def __init__(self, name, level=1, options=None, enable_stats=False, ttl=1000):
        if options is None:
            options = dict()
        self.name = name
        self.level = level
        self.ttl = ttl
        self.cache_dir = options.get(
            "cachePath", os.path.join(self.dataloop_path, "cache", name)
        )
        self.cache = Cache(directory=self.cache_dir)
        self.cache.stats(enable=enable_stats)

        self.conn = sqlite3.connect(os.path.join(self.cache_dir, 'cache.db'), check_same_thread=False)
        self.cursor = self.conn.cursor()

    @property
    def dataloop_path(self):
        return os.environ['DATALOOP_PATH'] if 'DATALOOP_PATH' in os.environ \
            else os.path.join(os.path.expanduser('~'), '.dataloop')

    def set(self, key, value):
        """
        set or add a key and value to the cache
        :param key: str or int type of key
        :param value: pickled value
        :return:
        """
        if not isinstance(key, str) and not isinstance(key, int):
            raise ValueError("key must be string or int")
        with Cache(self.cache.directory) as reference:
            reference.set(key=key, value=value, expire=self.ttl)

    def _key_fix(self, key):
        if '**' in key:
            key = key.replace('**', '%')
        if '*' in key:
            key = key.replace('*', '%')
        return key

    def list(self, pattern):
        """
        list the keys py pattern from the cache

        :param pattern: str or int type of key
        :return: the value of the key
        """
        self.cache.close()

        key = self._key_fix(pattern)

        try:
            self.cursor.execute("SELECT key FROM Cache WHERE key LIKE '{}'".format(key))

            rows = self.cursor.fetchall()
            for row in rows:
                for key in row:
                    yield key
        except:
            return None

    def ping(self):
        """
        Cache ping check if connection is working
        """
        if os.path.exists(os.path.join(self.cache_dir, 'cache.db')):
            return True
        else:
            raise Exception('cache db not fond')

    def get(self, key):
        """
        get the value of the key from the cache
        :param key: str or int type of key
        :return: the value of the key
        """
        self.cache.close()
        res = self.cache.get(key=key)
        if res is not None:
            try:
                return json.loads(res)
            except:
                return res

    def delete(self, key):
        """
        delete the element from the cache
        :param key: str or int type of key
        :return:
        """
        self.cache.close()
        self.cache.delete(key=key)

    def add(self, key, value):
        """
        add the element to the cache if the key is not already present.
        :param key: str or int type of key
        :param value: pickled value
        :return: bool: True if add False if not
        """
        if not isinstance(key, str) and not isinstance(key, int):
            raise ValueError("key must be string or int")
        self.cache.close()
        return self.cache.add(key=key, value=value, expire=self.ttl)

    def push(self, value):
        """
        push the element to the cache
        :param value: pickled value
        :return: bool: True if add False if not
        """
        self.cache.close()
        return self.cache.push(value=value, expire=self.ttl)

    def incr(self, key, value=1):
        """
        incremented the value of this key
        :param key: str or int type of key
        :param value: the amount of incremented
        :return:
        """
        self.cache.incr(key=key, delta=value)

    def decr(self, key, value=1):
        """
        decremented  the value of this key
        :param key: str or int type of key
        :param value: the amount of decremented
        :return:
        """
        self.cache.decr(key=key, delta=value)

    def pop(self, key):
        """
        delete the element from the cache and return it
        :param key: str or int type of key
        :return: the deleted element
        """
        self.cache.close()
        return self.cache.pop(key)

    def volume(self):
        """
        returns the estimated total size in bytes of the cache directory on disk.
        :return: size in bytes
        """
        return self.cache.volume()

    def clear(self):
        """
        simply removes all items from the cache.
        :return: number of the items
        """
        return self.cache.clear()

    def stats(self):
        """
        returns cache hits and misses.
        :return: tuple (hits, misses)
        """
        hits, misses = self.cache.stats(enable=False, reset=False)
        self.cache.stats(enable=True)
        return hits, misses

    def reset_stats(self):
        """
        reset cache hits and misses.
        :return:
        """
        self.cache.stats(enable=False, reset=True)
        self.cache.stats(enable=True)

    def keys(self):
        """
        return all the cache keys
        :return: list of the keys
        """
        for output in list(self.cache.iterkeys()):
            if output is not None:
                yield output

    def delete_cache(self):
        """
        Delete the cache folder
        """
        self.cache.close()
        import shutil

        try:
            shutil.rmtree(self.cache.directory)
        except OSError:  # Windows wonkiness
            pass
