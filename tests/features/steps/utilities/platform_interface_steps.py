import attr
import behave
import time
import jwt
import os
import shutil
import dtlpy as dl
import numpy as np
from behave_testrail_reporter import TestrailReporter
import filecmp

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
    if not hasattr(context.feature, 'to_delete_integrations_ids'):
        context.feature.to_delete_integrations_ids = list()
    if not hasattr(context, 'to_delete_drivers_ids'):
        context.to_delete_drivers_ids = list()
    if not hasattr(context, 'to_delete_datasets_ids'):
        context.to_delete_datasets_ids = list()
    if not hasattr(context, 'nodes'):
        context.nodes = list()
    if hasattr(context.feature, 'dataloop_feature_dl'):
        context.dl = context.feature.dataloop_feature_dl
    else:
        # get cookie name
        # feature_name = context.feature.name.replace(' ', '_')
        # api_counter_name = 'api_counter_{}.json'.format(feature_name)
        # api_counter_filepath = os.path.join(os.path.dirname(dl.client_api.cookie_io.COOKIE), api_counter_name)
        # # set counter
        # dl.client_api.set_api_counter(api_counter_filepath)

        # set context for run
        context.dl = dl

        # reset api counter
        # context.dl.client_api.calls_counter.on()
        # context.dl.client_api.calls_counter.reset()

        # set env to dev
        _, base_env = get_env_from_git_branch()
        if base_env != dl.client_api.environments[dl.client_api.environment]['alias']:
            context.dl.setenv(base_env)

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
            _, base_env = get_env_from_git_branch()
            current_branch = "{} - #{} Python {}".format(base_env, str(build_number), sys.version.split(" ")[0])  # Get the current build branch
            testrail_reporter = TestrailReporter(current_branch)
            context.config.reporters.append(testrail_reporter)


@behave.given(u'I create the dir path "{directory}"')
def step_impl(context, directory):
    context.new_path = os.path.join(os.environ['DATALOOP_TEST_ASSETS'], directory)
    try:
        if not os.path.exists(context.new_path):
            os.mkdir(context.new_path)
    except Exception as e:
        assert 'File exists' in e.args


@behave.then(u'I delete content in path path "{directory}"')
def step_impl(context, directory):
    context.content_path = os.path.join(os.environ['DATALOOP_TEST_ASSETS'], directory)

    for filename in os.listdir(context.content_path):
        file_path = os.path.join(context.content_path, filename)
        try:
            if os.path.isfile(file_path) or os.path.islink(file_path):
                os.unlink(file_path)
            elif os.path.isdir(file_path):
                shutil.rmtree(file_path)
        except Exception as e:
            print('Failed to delete %s. Reason: %s' % (file_path, e))


def compare_directory_files(dir1, dir2):
    """
    Compare two directories recursively. Files in each directory are
    assumed to be equal if their names and contents are equal.

    @param dir1: First directory path
    @param dir2: Second directory path

    @return: True if the directory trees are the same and
        there were no errors while accessing the directories or files,
        False otherwise.
   """

    dirs_cmp = filecmp.dircmp(dir1, dir2)
    if len(dirs_cmp.left_only) > 0 or len(dirs_cmp.right_only) > 0 or len(dirs_cmp.funny_files) > 0:
        return False
    (_, mismatch, errors) = filecmp.cmpfiles(
        dir1, dir2, dirs_cmp.common_files, shallow=False)
    if len(mismatch) > 0 or len(errors) > 0:
        return False
    for common_dir in dirs_cmp.common_dirs:
        new_dir1 = os.path.join(dir1, common_dir)
        new_dir2 = os.path.join(dir2, common_dir)
        if not compare_directory_files(new_dir1, new_dir2):
            return False
    return True


@behave.then(u'I compare between the dirs')
def step_impl(context):
    context.dir1 = None
    context.dir2 = None

    for parameter in context.table.rows:
        if parameter.cells[0] == "dir1":
            context.dir1 = os.path.join(os.environ['DATALOOP_TEST_ASSETS'], parameter.cells[1])

        if parameter.cells[0] == "dir2":
            context.dir2 = os.path.join(os.environ['DATALOOP_TEST_ASSETS'], parameter.cells[1])

    assert compare_directory_files(context.dir1, context.dir2)
