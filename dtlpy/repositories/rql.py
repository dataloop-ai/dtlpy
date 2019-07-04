from .. import PlatformException, entities


class Rql:
    def __init__(self, filters, resource='items', sort=None, updaate=None, delete=False, system_space=False,
                 page_offset=0, page_size=100):

        if not isinstance(filters, entities.Filters):
            raise PlatformException(
                error='400',
                message='"filter" must be type of repositories.Filters"')
        if resource not in ['items', 'annotations']:
            raise PlatformException(
                error='400',
                message='input "resource" must be "items" or "annotations". got "{}"'.format(resource))

        self.resource = resource
        self.filters = filters.prepare()
        self.page = page_offset
        self.page_size = page_size

    def prepare(self):
        return {'resource': self.resource,
                'filter': self.filters,
                'page': self.page,
                'pageSize': self.page_size}
