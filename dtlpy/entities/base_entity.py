from .. import miscellaneous


class BaseEntity(object):
    is_fetched = True

    def print(self, to_return=False, columns=None):
        """
        :param to_return:
        :param columns:
        """
        return miscellaneous.List([self]).print(to_return=to_return, columns=columns)

    def to_df(self, show_all=False, columns=None):
        """
        :param show_all:
        :param columns:
        """
        return miscellaneous.List([self]).to_df(show_all=show_all, columns=columns)

    # def __getattribute__(self, attr):
    #     if super(BaseEntity, self).__getattribute__(attr) is None:
    #         pass
    #     return super(BaseEntity, self).__getattribute__(attr)
