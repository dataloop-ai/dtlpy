
class BaseCache(object):
    def set(self, key, value):
        """
        set or add a key and value to the cache
        :param key: str or int type of key
        :param value: pickled value
        :return:
        """
        pass

    def get(self, key):
        """
        get the value of the key from the cache
        :param key: str or int type of key
        :return: the value of the key
        """
        pass

    def delete(self, key):
        """
        delete the element from the cache
        :param key: str or int type of key
        :return:
        """
        pass

    def keys(self):
        """
        return all the cache keys
        :return: list of the keys
        """
        pass