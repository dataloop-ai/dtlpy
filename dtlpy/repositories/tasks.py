import logging
import os
import json

from .. import services, entities, utilities


class Tasks(object):
    """
    Pipeliens repository
    """

    def __init__(self, project=None):
        self.logger = logging.getLogger('dataloop.tasks')
        self.client_api = services.ApiClient()
        self.project = project

    def create(self, pipeline_dict, name, description, triggers, input_parameters, output_parameters, projects,
               triggers_filter=None):
        """
        Create a new task
        :param pipeline_dict: dict of pipelines to add to task. {type: json_filepath}
        :param name: task name
        :param description:
        :param triggers: initiate session for task on triggers
        :param input_parameters: inputs for the task's sessions
        :param output_parameters: outputs for the task's sessions
        :param projects: projects to associate with task
        :return: Task entity
        """
        known_pipeline_types = ['init', 'main']
        pipelines = dict()
        for pipeline_type, pipeline_filepath in pipeline_dict.items():
            if pipeline_type not in known_pipeline_types:
                self.logger.exception(
                    'Unknown pipeline type: %s' % pipeline_type)
            if not os.path.isfile(pipeline_filepath):
                raise OSError('File doesnt exists. %s' % pipeline_filepath)
            with open(pipeline_filepath, 'r') as f:
                architecture_dict = json.load(f)
            pipelines[pipeline_type] = architecture_dict

        payload = {'name': name,
                   'pipeline': pipelines,
                   'metadata': {'system': {'description': description,
                                           'projects': projects}},
                   'triggers': triggers,
                   'input': input_parameters,
                   'output': output_parameters
                   }

        if triggers_filter:
            payload['triggersFilter'] = triggers_filter

        success, response = self.client_api.gen_request(req_type='post',
                                                        path='/tasks',
                                                        json_req=payload)
        if success:
            task = entities.Task(response.json())
        else:
            self.logger.exception('Platform error creating new task:')
            raise self.client_api.platform_exception
        return task

    def get(self, task_id=None, task_name=None):
        """
        Get a Pipeline object
        :param task_id: optional - search by id
        :param task_name: optional - search by name
        :return: Pipeline object
        """
        if task_id is not None:
            success, response = self.client_api.gen_request(req_type='get',
                                                            path='/tasks/%s' % task_id)
            if success:
                res = response.json()
                if len(res) > 0:
                    task = entities.Task(entity_dict=res)
                else:
                    task = None
            else:
                self.logger.exception('Platform error getting the task. id: %s' % task_id)
                raise self.client_api.platform_exception
        elif task_name is not None:
            tasks = self.list()
            task = [task for task in tasks if task.name == task_name]
            if len(task) == 0:
                self.logger.info('Pipeline not found. task id : %s' % task_name)
                task = None
            elif len(task) > 1:
                self.logger.warning('More than one task with same name. Please "get" by id')
                raise ValueError('More than one task with same name. Please "get" by id')
            else:
                task = task[0]
        else:
            self.logger.exception('Must input one search parameter!')
            raise ValueError('Must input one search parameter!')
        return task

    def delete(self, task_name=None, task_id=None):
        """
        Delete remote item
        :param task_name: optional - search item by remote path
        :param task_id: optional - search item by id
        :return:
        """
        if task_id is not None:
            success, response = self.client_api.gen_request(req_type='delete',
                                                            path='/tasks/%s' % task_id)
        elif task_name is not None:
            task = self.get(task_name=task_name)
            if task is None:
                self.logger.warning('task name was not found: name: %s' % task_name)
                raise ValueError('task name was not found: name: %s' % task_name)
            success, response = self.client_api.gen_request(req_type='delete',
                                                            path='/tasks/%s' % task.id)
        else:
            assert False
        return success

    def list(self):
        """
        List all task.
        :return: List of Pipeline objects
        """
        if self.project is None:
            success, response = self.client_api.gen_request(req_type='get',
                                                            path='/tasks')
        else:
            success, response = self.client_api.gen_request(req_type='get',
                                                            path='/tasks?projects=%s' % self.project.id)

        if success:
            tasks = utilities.List([entities.Task(entity_dict=entity_dict)
                                    for entity_dict in response.json()['items']])
            return tasks
        else:
            self.logger.exception('Platform error getting tasks')
            raise self.client_api.platform_exception

    def edit(self, task, system_metadata=False):
        """
        Edit an existing task
        :param task: Task entity
        :param system_metadata: bool
        :return: Task entity
        """
        url_path = '/tasks/%s' % task.id
        if system_metadata:
            url_path += '?system=true'
        success, response = self.client_api.gen_request(req_type='patch',
                                                        path=url_path,
                                                        json_req=task.to_dict())
        if success:
            return entities.Task(entity_dict=response.json())
        else:
            self.logger.exception('Platform error editing task. id: %s' % task.id)
            raise self.client_api.platform_exception
