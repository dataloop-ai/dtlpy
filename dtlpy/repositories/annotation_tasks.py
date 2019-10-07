import logging
from .. import exceptions
from .. import entities
from .. import utilities

logger = logging.getLogger(name=__name__)
URL_PATH = '/annotationtasks'


class AnnotationTasks:
    """
    AnnotationTasks repository
    """

    def __init__(self, client_api, project=None, dataset=None):
        self._client_api = client_api
        self.project = project
        self.dataset = dataset

    def list(self,
             project_ids=None,
             status=None,
             name=None,
             pages_size=None,
             page_offset=None,
             recipe=None,
             creator=None,
             assignments=None,
             min_date=None,
             max_date=None):
        """
        Get Annotation Task list

        :param name:
        :param project_ids: list of project ids
        :param assignments:
        :param creator:
        :param page_offset:
        :param pages_size:
        :param recipe:
        :param status:
        :param max_date: double
        :param min_date:double
        :return: List of Annotation Task objects
        """

        # url
        url = URL_PATH

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
        
        if assignments is not None:
            if not isinstance(assignments, list):
                assignments = [assignments]
            assignments = ','.join(assignments)
            query.append('assignments={}'.format(assignments))
        if status is not None:
            query.append('status={}'.format(status))
        if name is not None:
            query.append('name={}'.format(name))
        if pages_size is not None:
            query.append('pageSize={}'.format(pages_size))
        if page_offset is not None:
            query.append('pageOffset={}'.format(page_offset))
        if recipe is not None:
            query.append('recipe={}'.format(recipe))
        if creator is not None:
            query.append('creator={}'.format(creator))
        if min_date is not None:
            query.append('minDate={}'.format(min_date))
        if max_date is not None:
            query.append('maxDate={}'.format(max_date))

        if len(query) > 0:
            query_string = '&'.join(query)
            url = '{}?{}'.format(url, query_string)

        success, response = self._client_api.gen_request(req_type='get',
                                                         path=url)
        if success:
            annotation_tasks = utilities.List(
                [entities.AnnotationTask.from_json(client_api=self._client_api,
                                                   _json=_json)
                 for _json in response.json()['items']])
        else:
            logger.exception('Platform error getting annotation task')
            raise exceptions.PlatformException(response)

        return annotation_tasks

    def get(self, annotation_task_name=None, annotation_task_id=None):
        """
        Get an Annotation Task object
        :param annotation_task_name: optional - search by name
        :param annotation_task_id: optional - search by id
        :return: annotation_task_id object

        """

        # url
        url = URL_PATH

        if annotation_task_id is not None:
            url = '{}/{}'.format(url, annotation_task_id)
            success, response = self._client_api.gen_request(req_type='get',
                                                             path=url)
            if not success:
                raise exceptions.PlatformException('404', 'Annotation task not found')
            else:
                annotation_task = entities.AnnotationTask.from_json(_json=response.json(),
                                                                    client_api=self._client_api)
        elif annotation_task_name is not None:
            annotation_tasks = [annotation_task for annotation_task in self.list() if
                                annotation_task.name == annotation_task_name]
            if len(annotation_tasks) == 0:
                raise exceptions.PlatformException('404', 'Annotation task not found')
            elif len(annotation_tasks) > 1:
                raise exceptions.PlatformException('404',
                                                   'More than one Annotation task exist with the same name: {}'.format(
                                                       annotation_task_name))
            else:
                annotation_task = annotation_tasks[0]
        else:
            raise exceptions.PlatformException('400', 'Must provide either Annotation task name or Annotation task id')

        assert isinstance(annotation_task, entities.AnnotationTask)
        return annotation_task

    def delete(self, annotation_task=None, annotation_task_name=None, annotation_task_id=None):
        """
        Delete an Annotation Task
        :param annotation_task_id:
        :param annotation_task_name:
        :param annotation_task:

        :return: True
        """
        if annotation_task_id is None:
            if annotation_task is None:
                if annotation_task_name is None:
                    raise exceptions.PlatformException('400',
                                                       'Must provide either annotation task, '
                                                       'annotation task name or annotation task id')
                else:
                    annotation_task = self.get(annotation_task_name=annotation_task_name)
                    annotation_task_id = annotation_task.id

        url = URL_PATH
        url = '{}/{}'.format(url, annotation_task_id)
        success, response = self._client_api.gen_request(req_type='delete',
                                                         path=url)

        if not success:
            raise exceptions.PlatformException(response)
        return True

    def update(self, annotation_task=None):
        """
        Update an Annotation Task
        :return: Annotation Task object
        """
        url = URL_PATH
        url = '{}/{}'.format(url, annotation_task.id)
        success, response = self._client_api.gen_request(req_type='patch',
                                                         path=url,
                                                         json_req=annotation_task.to_json())
        if success:
            return entities.AnnotationTask.from_json(_json=response.json(),
                                                     client_api=self._client_api)
        else:
            raise exceptions.PlatformException(response)

    def create(self, name, status=None, project_id=None,
               dataset_id=None, recipe_id=None, assignments_ids=None,
               query=None, due_date=None):
        """
        Create a new Annotation Task
        :param assignments_ids:
        :param recipe_id:
        :param due_date:
        :param query:
        :param dataset_id:
        :param project_id:
        :param status:
        :param name:
        :return: Annotation Task object
        """
        payload = {'name': name}

        if status is not None:
            payload['status'] = status
        if project_id is not None:
            payload['projectId'] = project_id
        if dataset_id is not None:
            payload['dataset_id'] = dataset_id
        if recipe_id is not None:
            payload['recipe_id'] = recipe_id
        if assignments_ids is not None:
            if not isinstance(assignments_ids, list):
                assignments_ids = [assignments_ids]
            payload['assignments_ids'] = assignments_ids
        if query is not None:
            payload['query'] = query
        if due_date is not None:
            payload['dueDate'] = due_date

        success, response = self._client_api.gen_request(req_type='post',
                                                         path=URL_PATH,
                                                         data=payload)
        if success:
            annotation_task = entities.AnnotationTask.from_json(client_api=self._client_api,
                                                                _json=response.json())
        else:
            raise exceptions.PlatformException(response)
        assert isinstance(annotation_task, entities.AnnotationTask)
        return annotation_task
