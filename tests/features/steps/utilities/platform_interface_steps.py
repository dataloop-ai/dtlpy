import attr
import behave
import time
import jwt
import os
import dtlpy as dl
import numpy as np
from behave_testrail_reporter import TestrailReporter

dl.verbose.disable_progress_bar = True

try:
    # for local import
    from tests.env_from_git_branch import get_env_from_git_branch
except ImportError:
    # for remote import
    from env_from_git_branch import get_env_from_git_branch


@attr.s
class TimeKey:
    # For TestRail test-run
    _key = None

    @property
    def key(self):
        if self._key is None:
            self._key = time.strftime("%d-%m %H:%M")
        return self._key


time_key = TimeKey()


@behave.given('Platform Interface is initialized as dlp and Environment is set according to git branch')
def before_all(context):
    # set up lists to delete
    if not hasattr(context, 'to_delete_packages_ids'):
        context.to_delete_packages_ids = list()
    if not hasattr(context, 'to_delete_services_ids'):
        context.to_delete_services_ids = list()
    if not hasattr(context, 'to_delete_projects_ids'):
        context.to_delete_projects_ids = list()
    if not hasattr(context, 'to_delete_pipelines_ids'):
        context.to_delete_pipelines_ids = list()
    if not hasattr(context, 'to_delete_feature_set_ids'):
        context.to_delete_feature_set_ids = list()
    if not hasattr(context, 'to_delete_feature_ids'):
        context.to_delete_feature_ids = list()

    if hasattr(context.feature, 'dataloop_feature_dl'):
        context.dl = context.feature.dataloop_feature_dl
    else:
        # get cookie name
        feature_name = context.feature.name.replace(' ', '_')
        api_counter_name = 'api_counter_{}.json'.format(feature_name)
        api_counter_filepath = os.path.join(os.path.dirname(dl.client_api.cookie_io.COOKIE), api_counter_name)
        # set counter
        dl.client_api.set_api_counter(api_counter_filepath)

        # set context for run
        context.dl = dl

        # reset api counter
        context.dl.client_api.calls_counter.on()
        context.dl.client_api.calls_counter.reset()

        # set env to dev
        if get_env_from_git_branch() != dl.client_api.environments[dl.client_api.environment]['alias']:
            context.dl.setenv(get_env_from_git_branch())

        # check token
        payload = None
        for i in range(10):
            try:
                payload = jwt.decode(context.dl.token(), algorithms=['HS256'],
                                     verify=False, options={'verify_signature': False})
                break
            except jwt.exceptions.DecodeError:
                time.sleep(np.random.rand())
                pass

        allow_locally_with_user = os.environ.get('ALLOW_RUN_TESTS_LOCALLY_WITH_USER', 'false') == 'true'

        if not allow_locally_with_user and payload['email'] not in ['oa-test-4@dataloop.ai', 'oa-test-1@dataloop.ai',
                                                                    'oa-test-2@dataloop.ai',
                                                                    'oa-test-3@dataloop.ai']:
            assert False, 'Cannot run test on user: "{}". only test users'.format(payload['email'])

        # save to feature level
        context.feature.dataloop_feature_dl = context.dl

        avoid_testrail = os.environ.get('AVOID_TESTRAIL', 'false') == 'true'

        if not avoid_testrail and len(context.config.reporters) == 1:
            import sys
            build_number = os.environ.get('BITBUCKET_BUILD_NUMBER')
            current_branch = "{} - #{} Python {}".format(get_env_from_git_branch(), str(build_number), sys.version.split(" ")[0])  # Get the current build branch
            testrail_reporter = TestrailReporter(current_branch)
            context.config.reporters.append(testrail_reporter)
