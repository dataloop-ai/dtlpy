from .. import miscellaneous


class BaseEntity(object):
    is_fetched = True

    def __str__(self):
        return self.print()

    def print(self, to_return=False):
        return miscellaneous.List([self]).print(to_return=to_return)

    # def __getattribute__(self, attr):
    #     if super(BaseEntity, self).__getattribute__(attr) is None:
    #         pass
    #     return super(BaseEntity, self).__getattribute__(attr)
