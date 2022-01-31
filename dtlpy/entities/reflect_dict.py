class ReflectDict(dict):

    def __init__(self, value_type: type, on_access: callable = None):
        super(ReflectDict, self).__init__()
        self.value_type = value_type
        self.on_access = on_access

    def actual_keys(self):
        return super(ReflectDict, self).keys()

    def keys(self):
        last_yielded = None
        sorted_keys = list(super(ReflectDict, self).keys())
        sorted_keys.sort()
        for key in sorted_keys:
            if last_yielded is None:
                last_yielded = key
                yield key
            else:
                if last_yielded == key - 1:
                    last_yielded = key
                    yield key
                else:
                    while last_yielded < key:
                        last_yielded = last_yielded + 1
                        yield last_yielded

    def values(self):
        for key in self.keys():
            yield self[key]

    def items(self):
        for key in self.keys():
            yield key, self[key]

    def __iter__(self):
        return self.values()

    def __contains__(self, key):
        return key in list(self.keys())

    def __getitem__(self, key):
        requested_key = key
        if not isinstance(key, int):
            raise Exception('Key Error - key must be a frame number (integer)')

        if super(ReflectDict, self).__contains__(key):
            return super(ReflectDict, self).__getitem__(key)
        else:
            while key > 0:
                key = key - 1
                if super(ReflectDict, self).__contains__(key):
                    frame = super(ReflectDict, self).__getitem__(key)
                    if isinstance(frame, self.value_type):
                        if self.on_access is not None:
                            frame = self.on_access(self, actual_key=key, requested_key=requested_key, val=frame)
                        return frame
                    else:
                        raise Exception('Unknown value type, dict must be of type: {}'.format(
                            self.value_type))

    def __len__(self):
        return len(list(self.keys()))
