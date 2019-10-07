import logging
from .. import exceptions
from .. import entities
from .. import utilities

logger = logging.getLogger(name=__name__)


class Assignments:
    """
    Assignments repository
    """

    def __init__(self, client_api, project=None, task=None):
        self._client_api = client_api
        self.project = project
        self.task = task

    def list(self, project_ids=None, status=None, name=None, annotator=None, pages_size=None, page_offset=None):
        """
        Get Assignments list

        :param page_offset:
        :param pages_size:
        :param annotator:
        :param name:
        :param status:
        :param project_ids: list of project ids
        :return: List of Assignment objects
        """

        # url
        url = '/assignments'

        query = list()
        if project_ids is not None:
            if not isinstance(project_ids, list):
                project_ids = [project_ids]
        elif self.project is not None:
            project_ids = [self.project.id]
        else:
            raise ('400', 'Must provide project')
        project_ids = ','.join(project_ids)
        query.append('projects={}'.format(project_ids))
        
        if status is not None:
            query.append('status={}'.format(status))
        if name is not None:
            query.append('name={}'.format(name))
        if annotator is not None:
            query.append('annotator={}'.format(annotator))
        if pages_size is not None:
            query.append('pageSize={}'.format(pages_size))
        if page_offset is not None:
            query.append('pageOffset={}'.format(page_offset))

        if len(query) > 0:
            query_string = '&'.join(query)
            url = '{}?{}'.format(url, query_string)

        success, response = self._client_api.gen_request(req_type='get',
                                                         path=url)
        if success:
            assignments = utilities.List(
                [entities.Assignment.from_json(client_api=self._client_api,
                                               _json=_json)
                 for _json in response.json()['items']])
        else:
            logger.exception('Platform error getting assignments')
            raise exceptions.PlatformException(response)
        return assignments

    def get(self, assignment_name=None, assignment_id=None):
        """
        Get a Project object
        :param assignment_name: optional - search by name
        :param assignment_id: optional - search by id
        :return: Project object

        """

        if assignment_id is not None:
            url = '/assignments/{}'.format(assignment_id)
            success, response = self._client_api.gen_request(req_type='get',
                                                             path=url)
            if not success:
                raise exceptions.PlatformException('404', 'Assignment not found')
            else:
                assignment = entities.Assignment.from_json(_json=response.json(),
                                                           client_api=self._client_api)
        elif assignment_name is not None:
            assignments = [assignment for assignment in self.list() if assignment.name == assignment_name]
            if len(assignments) == 0:
                raise exceptions.PlatformException('404', 'Assignment not found')
            elif len(assignments) > 1:
                raise exceptions.PlatformException('404',
                                                   'More than one assignment exist with the same name: {}'.format(
                                                       assignment_name))
            else:
                assignment = assignments[0]
        else:
            raise exceptions.PlatformException('400', 'Must provide either assignment name or assignment id')

        assert isinstance(assignment, entities.Assignment)
        return assignment

    def delete(self, assignment=None, assignment_name=None, assignment_id=None):
        """
        Delete an assignment
        :param assignment_id:
        :param assignment_name:
        :param assignment:

        :return: True
        """
        if assignment_id is None:
            if assignment is None:
                if assignment_name is None:
                    raise exceptions.PlatformException('400',
                                                       'Must provide either assignment, '
                                                       'assignment name or assignment id')
                else:
                    assignment = self.get(assignment_name=assignment_name)
                    assignment_id = assignment.id
        url = '/assignments/{}'.format(assignment_id)
        success, response = self._client_api.gen_request(req_type='delete',
                                                         path=url)

        if not success:
            raise exceptions.PlatformException(response)
        return True

    def update(self, assignment=None):
        """
        Update an assignment
        :return: Assignment object
        """
        url = '/assignments/{}'.format(assignment.id)
        success, response = self._client_api.gen_request(req_type='patch',
                                                         path=url,
                                                         json_req=assignment.to_json())
        if success:
            return entities.Assignment.from_json(_json=response.json(),
                                                 client_api=self._client_api)
        else:
            raise exceptions.PlatformException(response)

    def create(self, name, annotator, status=None, project_id=None, metadata=None):
        """
        Create a new assignment
        :param metadata:
        :param project_id:
        :param status:
        :param annotator:
        :param name:
        :return: Assignment object
        """
        payload = {'name': name,
                   'annotator': annotator}

        if status is not None:
            payload['status'] = status
        if project_id is not None:
            payload['projectId'] = project_id
        if metadata is not None:
            payload['metadata'] = metadata

        success, response = self._client_api.gen_request(req_type='post',
                                                         path='/assignments',
                                                         data=payload)
        if success:
            assignment = entities.Assignment.from_json(client_api=self._client_api,
                                                    _json=response.json())
        else:
            raise exceptions.PlatformException(response)
        assert isinstance(assignment, entities.Assignment)
        return assignment
