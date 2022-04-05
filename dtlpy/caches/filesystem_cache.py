import os
import json
import glob
import shutil

from .base_cache import BaseCache


class FileSystemCache(BaseCache):
    def __init__(self, options=None, size=1000, ttl=1000):
        """
        docs
        """
        if options is None:
            options = {}
        root_dir = options.get('rootDir', os.environ['DEFAULT_CACHE_PATH'])
        if not os.path.isdir(root_dir):
            os.makedirs(root_dir, exist_ok=True)
        self.root_dir = root_dir
        self.ttl = ttl
        self.size = size

    def set(self, key, value):
        """
        set or add a key and value to the cache
        :param key: str or int type of key
        :param value: pickled value
        :return:
        """
        if not isinstance(key, str):
            raise ValueError("key must be string")
        filepath = os.path.join(self.root_dir, key + '.json')
        if not os.path.isdir(os.path.dirname(filepath)):
            os.makedirs(os.path.dirname(filepath), exist_ok=True)

        with open(filepath, 'w') as f:
            json.dump(value, f, indent=4)

    def list(self, key):
        """
        get the value of the key from the cache
        :param key: str or int type of key
        :return: the value of the key
        """
        if self.root_dir not in key:
            filepath = os.path.join(self.root_dir, key)
        else:
            filepath = key
        files_list = set(glob.glob(filepath + '.*', recursive=True))
        output_values = []
        for file in files_list:
            with open(file) as file_out:
                output_values.append(json.load(file_out))
        return output_values

    def get(self, key):
        """
        get the value of the key from the cache
        :param key: str or int type of key
        :return: the value of the key
        """
        if self.root_dir not in key:
            filepath = os.path.join(self.root_dir, key)
        else:
            filepath = key

        res = None
        if os.path.isfile(filepath):
            with open(filepath) as file_out:
                res = (json.load(file_out))
        return res

    def delete(self, key):
        """
        delete the element from the cache
        :param key: str or int type of key
        :return:
        """
        if self.root_dir not in key:
            filepath = os.path.join(self.root_dir, os.path.dirname(key))
        else:
            filepath = os.path.dirname(key)
        files_list = set(glob.glob(filepath, recursive=True))
        for file in files_list:
            if os.path.isdir(file):
                try:
                    shutil.rmtree(file)
                except OSError as e:
                    print("Error: %s - %s." % (e.filename, e.strerror))
