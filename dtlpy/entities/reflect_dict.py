class ReflectDict(dict):

    def __init__(self, value_type: type, start: int = None, end: int = None, on_access: callable = None):
        super(ReflectDict, self).__init__()
        self.value_type = value_type
        self.on_access = on_access
        self._start = int(start) if start is not None else 0
        self._end = int(end) if end is not None else 0

    @property
    def start(self):
        return self._start

    @start.setter
    def start(self, start):
        if not isinstance(start, float) and not isinstance(start, int):
            raise ValueError('Must input a valid number')
        self._start = int(start) if start is not None else 0

    @property
    def end(self):
        return self._end

    @end.setter
    def end(self, end):
        if not isinstance(end, float) and not isinstance(end, int):
            raise ValueError('Must input a valid number')
        self._end = int(end) if end is not None else 0

    def actual_keys(self):
        return super(ReflectDict, self).keys()

    def keys(self):
        sorted_keys = list(super(ReflectDict, self).keys())
        sorted_keys.sort()

        yield self._start
        last_yielded = self._start

        for key in sorted_keys:
            if last_yielded == key - 1:
                last_yielded = key
                yield key
            else:
                while last_yielded < key:
                    last_yielded = last_yielded + 1
                    yield last_yielded

        while last_yielded < self._end:
            last_yielded = last_yielded + 1
            yield last_yielded

    def values(self):
        for key in self.keys():
            yield self[key]

    def items(self):
        for key in self.keys():
            yield key, self[key]

    def __iter__(self):
        return self.keys()

    def __contains__(self, key):
        return key in list(self.keys())

    def __setitem__(self, key, value):
        if not isinstance(key, int):
            raise Exception('Key Error - key must be an integer')

        if key > self._end:
            self._end = key

        if key < self._start:
            self._start = key

        super(ReflectDict, self).__setitem__(key, value)

    def __getitem__(self, key):
        requested_key = key
        if not isinstance(key, int):
            raise Exception('Key Error - key must be an integer')

        if key < self._start or key > self._end:
            raise KeyError(key)
        elif super(ReflectDict, self).__contains__(key):
            return super(ReflectDict, self).__getitem__(key)
        else:
            while key > self._start:
                key = key - 1
                if super(ReflectDict, self).__contains__(key):
                    item = super(ReflectDict, self).__getitem__(key)
                    if isinstance(item, self.value_type):
                        if self.on_access is not None:
                            item = self.on_access(self, actual_key=key, requested_key=requested_key, val=item)
                        return item
                    else:
                        raise Exception('Unknown value type, dict must be of type: {}'.format(
                            self.value_type))

    def __len__(self):
        return len(list(self.keys()))
