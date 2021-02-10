import logging
from urllib.parse import urlencode
from .. import exceptions, entities, miscellaneous, services

logger = logging.getLogger(name=__name__)


class Webhooks:
    """
    Webhooks repository
    """

    def __init__(self,
                 client_api: services.ApiClient,
                 project: entities.Project = None):
        self._project = project
        self._client_api = client_api
        self._url = '/webhooks'

    ############
    # entities #
    ############
    @property
    def project(self) -> entities.Project:
        if self._project is None:
            raise exceptions.PlatformException(
                error='2001',
                message='Missing "project". need to set a Project entity or use project.webhooks repository')
        assert isinstance(self._project, entities.Project)
        return self._project

    @project.setter
    def project(self, project: entities.Project):
        if not isinstance(project, entities.Project):
            raise ValueError('Must input a valid Project entity')
        self._project = project

    ###########
    # methods #
    ###########
    def create(self,
               name: str,
               project_id: str = None,
               http_method=None,
               hook_url=None,
               project: entities.Project = None) -> entities.Webhook:
        """
        Create web hook entity
        :return:
        """
        if project is None:
            project = self._project

        if project_id is None and project is None:
            raise exceptions.PlatformException('400', 'Must provide project or project id')

        if project_id is None:
            project_id = project.id

        # payload
        payload = {
            'name': name,
            'httpMethod': http_method,
            'hookUrl': hook_url,
            'project': project_id
        }

        # request
        success, response = self._client_api.gen_request(req_type='post',
                                                         path=self._url,
                                                         json_req=payload)

        # exception handling
        if not success:
            raise exceptions.PlatformException(response)

        # return entity
        return entities.Webhook.from_json(_json=response.json(),
                                          client_api=self._client_api,
                                          project=project)

    def list(self, filters: entities.Filters = None) -> entities.PagedEntities:
        """
        List web hooks
        :return:
        """
        if filters is None:
            filters = entities.Filters(resource=entities.FiltersResource.WEBHOOK)
            if self._project is not None:
                filters.add(field='projectId', values=self._project.id)

        # assert type filters
        if not isinstance(filters, entities.Filters):
            raise exceptions.PlatformException('400', 'Unknown filters type')

        paged = entities.PagedEntities(items_repository=self,
                                       filters=filters,
                                       page_offset=filters.page,
                                       page_size=filters.page_size,
                                       client_api=self._client_api)
        paged.get_page()
        return paged

    def _build_entities_from_response(self, response_items) -> miscellaneous.List[entities.Webhook]:
        # handle execution
        pool = self._client_api.thread_pools(pool_name='entity.create')
        jobs = [None for _ in range(len(response_items))]
        # return execution list
        for i_item, item in enumerate(response_items):
            jobs[i_item] = pool.apply_async(entities.Webhook.from_json,
                                            kwds={'client_api': self._client_api,
                                                  '_json': item,
                                                  'project': self._project})
        # wait for all jobs
        _ = [j.wait() for j in jobs]

        # get all results
        items = miscellaneous.List([j.get() for j in jobs])
        return items

    def _list(self, filters: entities.Filters):
        """
        List web hooks
        :return:
        """

        query_params = {
            'pageOffset': filters.page,
            'pageSize': filters.page_size
        }

        url = self._url + '?{}'.format(
            urlencode({key: val for key, val in query_params.items() if val is not None}, doseq=True))

        # request
        success, response = self._client_api.gen_request(req_type='get',
                                                         path=url)

        if not success:
            raise exceptions.PlatformException(response)

        return response.json()

    def get(self, webhook_id=None, webhook_name=None) -> entities.Webhook:
        """
        Get Web hook

        :param webhook_name:
        :param webhook_id:
        :return: Web hook execution object
        """
        if webhook_id is None and webhook_name is None:
            raise exceptions.PlatformException('400', 'Must provide webhook_id or webhook_name id')
        elif webhook_id is None:
            webhooks_pages = self.list(
                filters=entities.Filters(field='name', values=webhook_name, resource=entities.FiltersResource.WEBHOOK))
            if webhooks_pages.items_count == 0:
                raise exceptions.PlatformException('404', 'Not found: web hook: {}'.format(webhook_name))
            elif webhooks_pages.items_count > 1:
                raise exceptions.PlatformException('404',
                                                   'More than one webhooks found: web hook: {}'.format(webhook_name))
            else:
                webhook = webhooks_pages.items[0]
        else:
            success, response = self._client_api.gen_request(
                req_type="get",
                path="{}/{}".format(self._url, webhook_id)
            )

            # exception handling
            if not success:
                raise exceptions.PlatformException(response)

            # return entity
            webhook = entities.Webhook.from_json(client_api=self._client_api,
                                                 _json=response.json(),
                                                 project=self._project)
            # verify input webhook name is same as the given id
            if webhook_name is not None and webhook.name != webhook_name:
                logger.warning(
                    "Mismatch found in webhooks.get: webhook_name is different then webhook.name:"
                    " {!r} != {!r}".format(
                        webhook_name,
                        webhook.name))

        return webhook

    def delete(self, webhook_id=None, webhook_name=None):
        """
        Delete Trigger object

        :param webhook_name:
        :param webhook_id:
        :return: True
        """
        if webhook_id is None:
            if webhook_name is None:
                raise exceptions.PlatformException('400', 'Must provide either webhook name or webhook id')
            else:
                webhook_id = self.get(webhook_name=webhook_name).id

        # request
        success, response = self._client_api.gen_request(
            req_type="delete",
            path="{}/{}".format(self._url, webhook_id)
        )
        # exception handling
        if not success:
            raise exceptions.PlatformException(response)
        return True

    def update(self, webhook: entities.Webhook) -> entities.Webhook:
        """

        :param webhook: Webhook entity
        :return: Webhook entity
        """
        assert isinstance(webhook, entities.Webhook)

        # payload
        payload = webhook.to_json()

        # request
        success, response = self._client_api.gen_request(req_type='patch',
                                                         path='{}/{}'.format(self._url, webhook.id),
                                                         json_req=payload)

        # exception handling
        if not success:
            raise exceptions.PlatformException(response)

        # return entity
        return entities.Webhook.from_json(_json=response.json(),
                                          client_api=self._client_api,
                                          project=self._project)
