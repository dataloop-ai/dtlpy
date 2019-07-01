import time
import behave
import dtlpy as dl
import jwt
import random
import shutil
import os
import json


@behave.given('Platform Interface is initialized as dlp and Environment is set to development')
def before_all(context):
    if hasattr(context.feature, 'dataloop_feature_dl'):
        context.dl = context.feature.dataloop_feature_dl
    else:
        # get cookie name
        feature_name = context.feature.name
        feature_name = feature_name.replace(' ', '_')
        num = random.randint(10000, 100000)
        cookie_name = 'cookie_{}_{}.json'.format(str(num), feature_name)
        new_cookie = os.path.join(os.path.dirname(dl.client_api.io.COOKIE), cookie_name)
        # copy to a new cookie
        if dl.client_api.io.COOKIE != new_cookie:
            shutil.copyfile(dl.client_api.io.COOKIE, new_cookie)
        # init new cookie
        dl.client_api.io.__init__(new_cookie)
        # remember cookie location
        context.feature.cookie_path = new_cookie
        # set call counter new cookie
        dl.client_api.calls_counter.cookie = dl.client_api.io

        # regular initiation procedure
        context.dl = dl
        context.dl.client_api.calls_counter.on()
        context.dl.client_api.calls_counter.reset()
        context.dl.setenv('dev')
        token = context.dl.token()
        payload = jwt.decode(token, algorithms=['HS256'], verify=False)
        if payload['email'] != 'oa-test-1@dataloop.ai':
            assert False, 'Cannot run test on user other than: oa-test-1@dataloop.ai'

        # save to feature level
        context.feature.dataloop_feature_dl = context.dl


@behave.given('There is a project by the name of "{project_name}"')
def step_impl(context, project_name):
    if hasattr(context.feature, 'dataloop_feature_project'):
        context.project = context.feature.dataloop_feature_project
    else:
        num = random.randint(10000, 100000)
        project_name = 'test_{}_{}'.format(str(num), project_name)
        context.project = context.dl.projects.create(project_name=project_name)
        context.feature.dataloop_feature_project = context.project
        time.sleep(5)
    context.dataset_count = 0


@behave.given('Clean up "{project_name}"')
def step_impl(context, project_name):
    #delete project
    context.project.delete(True, True)

    # update api call json
    api_calls_path = 'api_calls.json'
    api_calls_path = os.path.join(os.environ['DATALOOP_TEST_ASSETS'], api_calls_path)
    with open(api_calls_path, 'r') as f:
        api_calls = json.load(f)
    if context.feature.name in api_calls:
        api_calls[context.feature.name] += context.dl.client_api.calls_counter.number
    else:
        api_calls[context.feature.name] = context.dl.client_api.calls_counter.number
    with open(api_calls_path, 'w') as f:
        json.dump(api_calls, f)
    os.remove(context.feature.cookie_path)


@behave.given('Remove cookie')
def step_impl(context):
    os.remove(context.feature.cookie_path)
