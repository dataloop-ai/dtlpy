import logging

from .. import services, entities, utilities
import datetime
import anytree

logger = logging.getLogger('dataloop.pipelines')


class Sessions:
    """
        Sessions repository
    """

    def __init__(self, project=None):
        self.client_api = services.ApiClient()
        self.project = project

    def list(self):
        """
        A list of session for project
        :return:
        """
        success = self.client_api.gen_request('get', '/projects/%s/sessions' % self.project.id)
        if success:
            sessions = utilities.List(
                [entities.Session(entity_dict=entity_dict, project=self.project) for entity_dict in
                 self.client_api.last_response.json()])
        else:
            logger.exception('Platform error listing sessions')
            raise self.client_api.platform_exception
        return sessions

    def create(self, session_name, pipeline_id, dataset_id, package_id, previous_session=None):
        """
        Create a new session
        :param session_name:
        :param pipeline_id: pipeline for session
        :param dataset_id: dataset for session
        :param package_id: package for session
        :param previous_session: previous session if exists
        :return:
        """
        previous_session_id = None if previous_session is None else previous_session.id
        payload = {'name': session_name,
                   'dataset_id': dataset_id,
                   'pipe_id': pipeline_id,
                   'package_id': package_id,
                   'previous_session_id': previous_session_id}
        success = self.client_api.gen_request('post', '/projects/%s/sessions' % self.project.id, data=payload)
        if success:
            session = entities.Session(self.client_api.last_response.json(), self.project)
            return session
        else:
            logger.exception('Platform error creating a session')
            raise self.client_api.platform_exception

    def get(self, session_id=None, session_name=None):
        """
        Get a Session object
        :param session_id: optional - search by id
        :param session_name: optional - search by name
        :return:
        """
        if session_id is not None:
            success = self.client_api.gen_request('get', '/sessions/%s' % session_id)
            if success:
                res = self.client_api.last_response.json()
                if len(res) > 0:
                    session = entities.Session(entity_dict=res[0], project=self.project)
                else:
                    session = None
            else:
                logger.exception('Platform error getting session. id: %s' % session_id)
                raise self.client_api.platform_exception

        elif session_name is not None:
            sessions = self.list()
            session = [session for session in sessions if session.name == session_name]
            if len(session) == 0:
                logger.info('Session not found. session_name: %s' % session_name)
                session = None
            elif len(session) > 1:
                logger.exception('More than one session with same name. Please "get" by id')
                raise ValueError('More than one session with same name. Please "get" by id')
            else:
                session = session[0]
        else:
            logger.exception('Must choose by at least one. "session_id" or "session_name"')
            raise ValueError('Must choose by at least one. "session_id" or "session_name"')
        return session

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
            logger.exception('Must choose by at least one. "session_id" or "session"')
            raise ValueError('Must choose by at least one. "session_id" or "session"')
        success = self.client_api.gen_request('delete', '/sessions/%s' % session_id)
        if not success:
            logger.exception('Platform error deleting a session:')
            raise self.client_api.platform_exception
        return True

    def tree(self):
        """
        Print sessions tree
        :return:
        """
        if self.project is None:
            logger.exception('Cant print project tree and project doesnt exist')
            raise ValueError('Cant print project tree and project doesnt exist')
        sessions = self.list()

        sorted_sessions = sorted(sessions, key=lambda k: k.createdAt, reverse=False)

        # recursive function to get all previous sessions
        def add_session_node(w_session_dict_by_id, session_id, w_sessions_dict_tree):
            # cehck if session is in sessions dictionary
            if session_id not in w_session_dict_by_id:
                w_session_dict_by_id[session_id] = self.get(session_id=session_id)

            # get session from sessions dictionary
            w_session = w_session_dict_by_id[session_id]
            # check if exists in tree dictioanry
            if w_session.id not in w_sessions_dict_tree:
                # insert previous session
                node_name = '%s: %s: %s' % \
                            (w_session.name,
                             datetime.datetime.fromtimestamp(int(str(w_session.createdAt)[:-3])).strftime(
                                 '%Y-%m-%d %H:%M:%S'),
                             w_session.id)
                # if previous session exists - add it as node
                if w_session.previous_session is not None:
                    w_sessions_dict_tree = add_session_node(w_session_dict_by_id=w_session_dict_by_id,
                                                            session_id=w_session.previous_session,
                                                            w_sessions_dict_tree=w_sessions_dict_tree)
                    w_sessions_dict_tree[w_session.id] = anytree.Node(node_name,
                                                                      w_sessions_dict_tree[w_session.previous_session])
                # add node without previous session
                else:
                    w_sessions_dict_tree[w_session.id] = anytree.Node(node_name)
            return w_sessions_dict_tree

        # create a dict with all session from project
        session_dict_by_id = dict()
        for session in sorted_sessions:
            session_dict_by_id[session.id] = session

        sessions_dict_tree = dict()
        for session in sorted_sessions:
            add_session_node(w_session_dict_by_id=session_dict_by_id,
                             session_id=session.id,
                             w_sessions_dict_tree=sessions_dict_tree)

        for key in list(sessions_dict_tree.keys()):
            if sessions_dict_tree[key].parent is None:
                for pre, fill, node in anytree.RenderTree(sessions_dict_tree[key]):
                    pre = pre.replace('─', '-').replace('└', '|').replace('├', '|').replace('│', '|')
                    logger.info("%s%s" % (pre, node.name))

    def run(self, session_id=None, session_name=None, input_params=None, remote_run=False):
        """
        Run a session
        :param session_id:
        :param session_name:
        :param input_params:
        :param remote_run:
        :return:
        """
        from ..pipelines import PipelineRunner
        from ..platform_interface import PlatformInterface

        if input_params is None:
            input_params = dict()

        session = self.get(session_id=session_id, session_name=session_name)
        if session is None:
            logger.exception('cant run session. session_id: %s' % session.id)
            assert False

        # when call to run_pipe from run_pipe_from_previous_session the following params should be set from there.
        # if run_pipe without previous - those should be false
        if 'weights_from_prev' not in input_params:
            input_params['weights_from_prev'] = False
        if 'conf_from_prev' not in input_params:
            input_params['conf_from_prev'] = False

        if remote_run:
            # TODO
            pass

        else:
            print('[INFO] Running sessions locally:')
            # run locally
            # Run pipeline
            pipeline_runner = PipelineRunner(PlatformInterface())
            # load pipe from yml
            pipeline_runner.from_pipeline_id(session.pipeline)
            outs = pipeline_runner.run(**input_params)

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
        dataset_id = self.get_dataset(dataset_name=dataset_name, project_name=project_name).id

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
