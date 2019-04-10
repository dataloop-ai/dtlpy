import logging
import datetime
import anytree
import json
from urllib.parse import urlencode

from .. import services, entities, utilities, repositories


class Sessions:
    """
    Sessions repository
    """

    def __init__(self, task=None):
        self.logger = logging.getLogger('dataloop.pipelines')
        self.client_api = services.ApiClient()
        self.task = task

    def list(self):
        """
        A list of session for project
        :return:
        """
        if self.task is None:
            raise ValueError('cant list sessions without task id')
        success = self.client_api.gen_request(req_type='get',
                                              path='/tasks/%s/sessions' % self.task.id)
        if success:
            sessions = utilities.List(
                [entities.Session(entity_dict=entity_dict) for entity_dict in
                 self.client_api.last_response.json()['items']])
        else:
            self.logger.exception('Platform error listing sessions')
            raise self.client_api.platform_exception
        return sessions

    def get(self, session_id):
        """
        Get a Session object
        :param session_id: optional - search by id
        :param session_name: optional - search by name
        :return:
        """
        success = self.client_api.gen_request(req_type='get', path='/sessions/%s' % session_id)
        if success:
            res = self.client_api.last_response.json()
            if len(res) > 0:
                session = entities.Session(entity_dict=res)
            else:
                session = None
        else:
            self.logger.exception(
                'Platform error getting session. id: %s' % session_id)
            raise self.client_api.platform_exception
        return session

    def create(self, input_parameters):
        """
        Create a new session
        :param session_name:
        :param pipeline_id: pipeline for session
        :param dataset_id: dataset for session
        :param package_id: package for session
        :param previous_session: previous session if exists
        :return:
        """
        if self.task is None:
            raise ValueError('cant create a session without task id')
        if not isinstance(input_parameters, dict):
            raise ValueError('input must be a dictionary')
        success = self.client_api.gen_request(req_type='post',
                                              path='/tasks/%s/sessions' % self.task.id,
                                              json_req=input_parameters)
        if success:
            session = entities.Session(entity_dict=self.client_api.last_response.json())
            return session
        else:
            self.logger.exception('Platform error creating a session')
            raise self.client_api.platform_exception
    #
    # def tree(self):
    #     """
    #     Print sessions tree
    #     :return:
    #     """
    #     if self.project is None:
    #         self.logger.exception('Cant print project tree and project doesnt exist')
    #         raise ValueError('Cant print project tree and project doesnt exist')
    #     sessions = self.list()
    #
    #     sorted_sessions = sorted(
    #         sessions, key=lambda k: k.createdAt, reverse=False)
    #
    #     # recursive function to get all previous sessions
    #     def add_session_node(w_session_dict_by_id, session_id, w_sessions_dict_tree):
    #         # cehck if session is in sessions dictionary
    #         if session_id not in w_session_dict_by_id:
    #             w_session_dict_by_id[session_id] = self.get(
    #                 session_id=session_id)
    #
    #         # get session from sessions dictionary
    #         w_session = w_session_dict_by_id[session_id]
    #         # check if exists in tree dictioanry
    #         if w_session.id not in w_sessions_dict_tree:
    #             # insert previous session
    #             node_name = '%s: %s: %s' % \
    #                         (w_session.name,
    #                          datetime.datetime.fromtimestamp(int(str(w_session.createdAt)[:-3])).strftime(
    #                              '%Y-%m-%d %H:%M:%S'),
    #                          w_session.id)
    #             # if previous session exists - add it as node
    #             if w_session.previous_session is not None:
    #                 w_sessions_dict_tree = add_session_node(w_session_dict_by_id=w_session_dict_by_id,
    #                                                         session_id=w_session.previous_session,
    #                                                         w_sessions_dict_tree=w_sessions_dict_tree)
    #                 w_sessions_dict_tree[w_session.id] = anytree.Node(node_name,
    #                                                                   w_sessions_dict_tree[w_session.previous_session])
    #             # add node without previous session
    #             else:
    #                 w_sessions_dict_tree[w_session.id] = anytree.Node(
    #                     node_name)
    #         return w_sessions_dict_tree
    #
    #     # create a dict with all session from project
    #     session_dict_by_id = dict()
    #     for session in sorted_sessions:
    #         session_dict_by_id[session.id] = session
    #
    #     sessions_dict_tree = dict()
    #     for session in sorted_sessions:
    #         add_session_node(w_session_dict_by_id=session_dict_by_id,
    #                          session_id=session.id,
    #                          w_sessions_dict_tree=sessions_dict_tree)
    #
    #     for key in list(sessions_dict_tree.keys()):
    #         if sessions_dict_tree[key].parent is None:
    #             for pre, fill, node in anytree.RenderTree(sessions_dict_tree[key]):
    #                 pre = pre.replace('─', '-').replace('└',
    #                                                     '|').replace('├', '|').replace('│', '|')
    #                 self.logger.info("%s%s" % (pre, node.name))

    def run(self,
            session_id=None,
            session=None,
            pipelines_to_run=None,
            remote_run=False,
            reporter=None):
        """
        Run a session.
        Must supply exactly one: "session_id" or "session"
        :param session_id: session id
        :param session: Session object
        :param remote_run:
        :param pipelines_to_run: list of pipeline types to run
        :param pipelines_not_to_run: list of pipeline types to skip
        :return:
        """
        from ..pipelines import PipelineRunner
        from ..platform_interface import PlatformInterface

        if session_id is None and session is None or \
                session_id is not None and session is not None:
            # check that exactly one exists
            self.logger.exception(
                'Must supply exactly one of inputs: "session_id" or "session"')
            raise ValueError(
                'Must supply exactly one of inputs: "session_id" or "session"')

        if session_id is not None:
            session = self.get(session_id=session_id)
        if session is None:
            self.logger.exception(
                'cant run session. session_id: %s' % session.id)
            assert False

        # when call to run_pipe from run_pipe_from_previous_session the following params should be set from there.
        # if run_pipe without previous - those should be false
        # if 'weights_from_prev' not in input_params:
        #     input_params['weights_from_prev'] = False
        # if 'conf_from_prev' not in input_params:
        #     input_params['conf_from_prev'] = False

        if remote_run:
            # TODO
            pass

        else:
            run_pipelines_types = ['init', 'main']
            if pipelines_to_run is None:
                # run all
                pass
            if pipelines_to_run is not None:
                # get only the ones to run
                for pipeline in run_pipelines_types:
                    if pipeline not in pipelines_to_run:
                        run_pipelines_types.remove(pipeline)

            # run locally
            self.logger.info('Running session. session_id: %s' % session.id)
            tasks_repo = repositories.Tasks()
            task = tasks_repo.get(task_id=session.taskId)
            pipelines = task.pipeline
            for pipeline_type in run_pipelines_types:
                if pipeline_type not in pipelines:
                    # pipelines type doesnt exists in task
                    continue
                if pipeline_type not in run_pipelines_types:
                    # skip pipeline: pipeline type not in run_pipelines_types
                    self.logger.info(
                        'Skipping pipeline type: %s' % pipeline_type)
                    continue
                pipeline_dict = pipelines[pipeline_type]
                self.logger.info('Running pipeline type: %s' % pipeline_type)
                # Run pipeline
                pipeline_runner = PipelineRunner(PlatformInterface(), reporter=reporter)
                # load pipe from yml
                pipeline_runner.from_dictionary(pipeline_dict)
                # get pipelines context
                current_inputs = pipeline_runner.pipeline_builder.get_context()
                current_context = dict()
                session.input['platform_interface'] = pipeline_runner.platform_interface
                session.input['session_id'] = session.id
                if reporter is not None:
                    session.input['globals_msg_thread_queue'] = reporter.queue
                for key, val in session.input.items():
                    current_context[key] = val
                out_context = pipeline_runner.run(context=current_context)
                # handle session's outputs
                session_outs = dict()
                for out_obj in task.output:
                    if out_obj['from'] not in out_context:
                        self.logger.error('missing session\'s output from context. from: %s' % out_obj['from'])
                        continue
                    session_outs[out_obj['path']] = out_context[out_obj['from']]
                if reporter is not None:
                    reporter.send_progress({'output': session_outs})

    def run_from_previous(self, prev_session_id, config_filename=None, input_params=None, pipe_id=None,
                          project_name=None, dataset_name=None, session_name=None, package_id=None,
                          remote_run=False):
        """
        Create and run a new session based on a previous one.
        Input arguments will replace the previous session's parameters in the new one
        :param prev_session_id:
        :param config_filename:
        :param input_params:
        :param pipe_id:
        :param project_name:
        :param dataset_name:
        :param session_name:
        :param package_id:
        :param remote_run:
        :return:
        """
        session_params = self.sessions_info(session_id=prev_session_id)
        assert len(session_params) == 1, '[ERROR]'
        session_params = session_params[0]

        #######################################
        # Take params from prev or from input #
        project_id = self.get_project(project_name=project_name).id
        dataset_id = self.get_dataset(
            dataset_name=dataset_name, project_name=project_name).id

        if pipe_id is None:
            pipe_id = session_params['pipe']
        if session_name is None:
            session_name = session_params['name']
        if package_id is None:
            package_id = session_params['package']

        ######################
        # Create new session #
        ######################
        res = self.sessions_create(session_name=session_name,
                                   pipe_id=pipe_id,
                                   previous_session_id=prev_session_id,
                                   project_id=project_id,
                                   dataset_id=dataset_id,
                                   package_id=package_id)
        assert res
        session_id = self.last_response.json()['id']

        # define location of input to pipe
        input_params['weights_from_prev'] = True
        input_params['conf_from_prev'] = True
        if config_filename is not None:
            # check if new configuration file was inputted
            input_params['conf_from_prev'] = False
            self.sessions_artifact_upload(session_id=session_id,
                                          filename=config_filename,
                                          artifact_type='conf',
                                          description='configuration for model in session')

        self.run(session_id=session_id,
                 input_params=input_params,
                 remote_run=remote_run)

    def edit(self):
        pass

    def delete(self, session_id=None, session=None):
        """
        Delete a session
        :param session_id: optional - search by id
        :param session: optional - Session object
        :return:
        """
        if session_id is not None:
            pass
        elif session is not None and isinstance(session, entities.Session):
            session_id = session.id
        else:
            self.logger.exception(
                'Must choose by at least one. "session_id" or "session"')
            raise ValueError(
                'Must choose by at least one. "session_id" or "session"')
        success = self.client_api.gen_request(
            'delete', '/sessions/%s' % session_id)
        if not success:
            self.logger.exception('Platform error deleting a session:')
            raise self.client_api.platform_exception
        return True
