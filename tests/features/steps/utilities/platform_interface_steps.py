import time
import behave
import dtlpy as dl
import jwt


@behave.given('Platform Interface is initialized as dlp and Environment is set to development')
def step_impl(context):
    context.dlp = dl
    context.dlp.setenv('dev')
    token = context.dlp.token()
    payload = jwt.decode(token, algorithms=['HS256'], verify=False)
    if payload['email'] != 'oa-test-1@dataloop.ai':
        assert False, 'Cannot run test on user other than: oa-test-1@dataloop.ai'


@behave.given('There is a project by the name of "{project_name}"')
def step_impl(context, project_name):
    context.project = context.dlp.projects.create(project_name=project_name)
    time.sleep(5)  # to sleep because authorization takes time
    context.dataset_count = 0
