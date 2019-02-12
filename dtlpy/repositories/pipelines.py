import logging
import os
import yaml

from .. import services, entities, utilities

logger = logging.getLogger('dataloop.pipelines')


class Pipelines(object):
    """
    Pipeliens repository
    """

    def __init__(self):
        self.client_api = services.ApiClient()
        self.pipes = list()

    def create(self, filepath, name, description, pipe_type):
        """
        Create a new pipeline
        :param filepath: local pipeline yml file
        :param name: pipeline name
        :param description:
        :param pipe_type:
        :return:
        """
        if not os.path.isfile(filepath):
            raise OSError('File doesnt exists. %s' % filepath)
        with open(filepath, 'r') as f:
            arch_dict = yaml.load(f)
        payload = {'name': name, 'arch': yaml.dump(arch_dict), 'description': description, 'type': pipe_type}

        success = self.client_api.gen_request('post', '/pipes', data=payload)
        if success:
            pipeline = entities.Pipeline(self.client_api.last_response.json())
        else:
            logger.exception('Platform error creating new pipeline:')
            raise self.client_api.platform_exception
        return pipeline

    def get(self, pipeline_id=None, pipeline_name=None):
        """
        Get a Pipeline object
        :param pipeline_id: optional - search by id
        :param pipeline_name: optional - search by name
        :return: Pipeline object
        """
        if pipeline_id is not None:
            success = self.client_api.gen_request('get', '/pipes/%s' % pipeline_id)
            if success:
                res = self.client_api.last_response.json()
                if len(res) > 0:
                    pipeline = entities.Pipeline(entity_dict=res[0])
                else:
                    pipeline = None
            else:
                logger.exception('Platform error getting the pipeline. id: %s' % pipeline_id)
                raise self.client_api.platform_exception
        elif pipeline_name is not None:
            pipelines = self.list()
            pipeline = [pipeline for pipeline in pipelines if pipeline.name == pipeline_name]
            if len(pipeline) == 0:
                logger.info('Pipeline not found. pipeline id : %s' % pipeline_name)
                pipeline = None
            elif len(pipeline) > 1:
                logger.warning('More than one pipeline with same name. Please "get" by id')
                raise ValueError('More than one pipeline with same name. Please "get" by id')
            else:
                pipeline = pipeline[0]
        else:
            logger.exception('Must input one search parameter!')
            raise ValueError('Must input one search parameter!')
        return pipeline

    def delete(self, pipe_id):
        pass
        # return self.client_api.gen_request('delete', '/pipes/%s' % pipe_id)

    def list(self):
        """
        List all pipeline.
        :return: List of Pipeline objects
        """
        success = self.client_api.gen_request('get', '/pipes')
        if success:
            self.pipes = utilities.List(
                [entities.Pipeline(entity_dict=entity_dict) for entity_dict in self.client_api.last_response.json()])
            return self.pipes
        else:
            logger.exception('Platform error getting pipelines')
            raise self.client_api.platform_exception

    def edit(self, filepath, pipe_id, description=None, name=None):
        """
        Edit an existing pipeline
        :param filepath: new pipeline configuration yml file
        :param pipe_id: id of existing pipelien
        :param description: new description
        :param name: new name
        :return: Edited Pipeline object
        """
        payload = dict()
        if filepath is not None:
            with open(filepath, 'r') as f:
                arch_dict = yaml.load(f)
            payload['arch'] = yaml.dump(arch_dict)
        if description is not None:
            payload['description'] = description
        if name is not None:
            payload['name'] = name
        if len(payload) == 0:
            raise ValueError('Must edit at least one value')
        success = self.client_api.gen_request('patch', '/pipes/%s' % pipe_id, json_req=payload)
        if success:
            return True
        else:
            logger.exception('Platform error editing pipeline: id: %s' % pipe_id)
            raise self.client_api.platform_exception
