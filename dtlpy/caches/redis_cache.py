import redis
import json
import datetime
from .base_cache import BaseCache


class RedisCache(BaseCache):
    def __init__(self, options=None, ttl=1000):
        if options is None:
            options = {}
        self.cache = redis.Redis(
            host=options.get('host', '127.0.0.1'),
            port=options.get('port', 6379),
            socket_keepalive=options.get('keepalive', True)
        )
        self.ttl = ttl

    def set(self, key, value):
        """
        set or add a key and value to the cache
        :param key: str or int type of key
        :param value: pickled value
        :return:
        """
        if not isinstance(key, str):
            raise ValueError("key must be string")
        self.cache.setex(name=key, value=value, time=self.ttl)

    def ping(self):
        """
        Cache ping check if connection is working
        """
        self.cache.ping()

    def list(self, pattern):
        """
        get the value of the key from the cache
        :param pattern: str or int type of key
        :return: the value of the key
        """
        if '\\' in pattern:
            pattern = pattern.replace('\\', '\\\\')
        keys_list = self.cache.keys(pattern=r'{}'.format(pattern))
        for key in keys_list:
            yield key.decode("UTF-8")

    def get(self, key):
        """
        get the value of the key from the cache
        :param key: str or int type of key
        :return: the value of the key
        """
        res = self.cache.get(r'{}'.format(key))
        if res is not None:
            try:
                return json.loads(res.decode("UTF-8"))
            except:
                return res.decode("UTF-8")

    def delete(self, key):
        """
        delete the element from the cache
        :param key: str or int type of key
        :return:
        """
        self.cache.delete(key)

    def keys(self):
        """
        return all the cache keys
        :return: list of the keys
        """
        for output in list(self.cache.keys()):
            if output is not None:
                yield output.decode('utf-8')

    def clear(self):
        """
        return all the cache keys
        :return: list of the keys
        """
        all_keys = self.cache.keys('*')
        for k in all_keys:
            self.cache.delete(k)
