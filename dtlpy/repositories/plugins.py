import logging

from .. import entities, utilities, PlatformException


class Plugins(object):
    """
        Plugins repository
    """

    def __init__(self, client_api, project=None):
        self.logger = logging.getLogger('dataloop.plugins')
        self.client_api = client_api
        self.project = project

    def create(self, name, package, input_parameters, output_parameters):
        """
        Create a new plugin
        :param name: plugin name
        :param input_parameters: inputs for the plugin's sessions
        :param output_parameters: outputs for the plugin's sessions
        :param package: packageId:version
        :return: plugin entity
        """
        if isinstance(input_parameters, entities.PluginInput):
            input_parameters = [input_parameters]
        if not isinstance(input_parameters, list):
            raise TypeError('must be a list of PluginInput')
        # if not all(isinstance(n, entities.PluginInput) for n in input_parameters):
        #     raise TypeError('must be a list of PluginInput')

        # input_parameters = [p.to_json for p in input_parameters]
        input_parameters.append({'path': 'package',
                                 'resource': 'package',
                                 'by': 'ref',
                                 'constValue': package})
        payload = {'name': name,
                   'pipeline': dict(),
                   'input': input_parameters,
                   'output': output_parameters,
                   'metadata': {'system': {
                       "projects": [self.project.id]
                   }}
                   }

        success, response = self.client_api.gen_request(req_type='post',
                                                        path='/tasks',
                                                        json_req=payload)
        if success:
            plugin = entities.Plugin.from_json(client_api=self.client_api,
                                               _json=response.json())
        else:
            self.logger.exception('Platform error creating new plugin:')
            raise PlatformException(response)
        return plugin

    def get(self, plugin_id=None, plugin_name=None):
        """
        Get a Pipeline object
        :param plugin_id: optional - search by id
        :param plugin_name: optional - search by name
        :return: Pipeline object
        """
        if plugin_id is not None:
            success, response = self.client_api.gen_request(req_type='get',
                                                            path='/tasks/%s' % plugin_id)
            if success:
                res = response.json()
                if len(res) > 0:
                    plugin = entities.Plugin.from_json(client_api=self.client_api, _json=res)
                else:
                    plugin = None
            else:
                self.logger.exception('Platform error getting the plugin. id: %s' % plugin_id)
                raise PlatformException(response)
        elif plugin_name is not None:
            plugins = self.list()
            plugin = [plugin for plugin in plugins if plugin.name == plugin_name]
            if len(plugin) == 0:
                self.logger.info('Pipeline not found. plugin id : %s' % plugin_name)
                plugin = None
            elif len(plugin) > 1:
                self.logger.warning('More than one plugin with same name. Please "get" by id')
                raise ValueError('More than one plugin with same name. Please "get" by id')
            else:
                plugin = plugin[0]
        else:
            self.logger.exception('Must input one search parameter!')
            raise ValueError('Must input one search parameter!')
        return plugin

    def delete(self, plugin_name=None, plugin_id=None):
        """
        Delete remote item
        :param plugin_name: optional - search item by remote path
        :param plugin_id: optional - search item by id
        :return:
        """
        if plugin_id is not None:
            success, response = self.client_api.gen_request(req_type='delete',
                                                            path='/tasks/%s' % plugin_id)
        elif plugin_name is not None:
            plugin = self.get(plugin_name=plugin_name)
            if plugin is None:
                self.logger.warning('plugin name was not found: name: %s' % plugin_name)
                raise ValueError('plugin name was not found: name: %s' % plugin_name)
            success, response = self.client_api.gen_request(req_type='delete',
                                                            path='/tasks/%s' % plugin.id)
        else:
            assert False
        return success

    def list(self):
        """
        List all plugin.
        :return: List of Pipeline objects
        """
        if self.project is None:
            success, response = self.client_api.gen_request(req_type='get',
                                                            path='/tasks')
        else:
            success, response = self.client_api.gen_request(req_type='get',
                                                            path='/tasks?projects=%s' % self.project.id)

        if success:
            plugins = utilities.List(
                [entities.Plugin.from_json(client_api=self.client_api,
                                           _json=_json)
                 for _json in response.json()['items']])
            return plugins
        else:
            self.logger.exception('Platform error getting plugins')
            raise PlatformException(response)

    def edit(self, plugin, system_metadata=False):
        """
        Edit an existing plugin
        :param plugin: Plugin entity
        :param system_metadata: bool
        :return: Plugin entity
        """
        url_path = '/tasks/%s' % plugin.id
        if system_metadata:
            url_path += '?system=true'
        success, response = self.client_api.gen_request(req_type='patch',
                                                        path=url_path,
                                                        json_req=plugin.to_json())
        if success:
            return entities.Plugin.from_json(client_api=self.client_api,
                                             _json=response.json())
        else:
            self.logger.exception('Platform error editing plugin. id: %s' % plugin.id)
            raise PlatformException(response)
