import behave
import random
import dtlpy as dl
import subprocess
import os
import time


@behave.given(u"I am logged in")
def step_impl(context):
    assert not dl.client_api.token_expired()


@behave.given(u'Environment is "dev"')
def step_impl(context):
    dl.setenv('dev')


@behave.when(u"I perform command")
def step_impl(context):
    rel_path = os.environ['DATALOOP_TEST_ASSETS']

    # fix params
    for column in context.table.headings:
        index = context.table.get_column_index(column_name=column)
        column = column.replace("<random>", context.random)
        column = column.replace("<rel_path>", rel_path)
        context.table.headings[index] = column

    # set cmds
    cmds = ['dlp']
    cmds += context.table.headings

    # if list try 4 times
    num_tries = 1
    if '-p' in cmds:
        num_tries = 4

    # run command
    time.sleep(1)
    for i in range(num_tries):
        # run shell command
        p = subprocess.Popen(cmds, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        context.out, context.err = p.communicate()
        if p.returncode == 0:
            break

    # save return code
    context.return_code = p.returncode

    # debug
    if context.return_code != 0:
        if context.err is not None:
            print(context.err.decode('utf-8'))
        if context.out is not None:
            print(context.out.decode('utf-8'))


@behave.then(u'There is a project by the name of "{project_name}"')
def step_impl(context, project_name):
    assert isinstance(project_name, str)
    project_name = project_name.replace("<random>", context.random)
    context.dl.projects.get(project_name=project_name)


@behave.then(u"I succeed")
def step_impl(context):
    assert context.return_code == 0


@behave.when(u"I succeed")
def step_impl(context):
    assert context.return_code == 0


@behave.then(u"I dont succeed")
def step_impl(context):
    assert context.return_code != 0


@behave.given(u"I have context random number")
def step_impl(context):
    if not hasattr(context.feature, 'random'):
        context.feature.random = str(random.randrange(1000, 100000))
    context.random = context.feature.random


@behave.given(u'I delete the project by the name of "{project_name}"')
def step_impl(context, project_name):
    assert isinstance(project_name, str)
    project_name = project_name.replace("<random>", context.random)
    project = context.dl.projects.get(project_name=project_name)
    project.delete(True, True)


@behave.then(u'I wait "{seconds}"')
def step_impl(context, seconds):
    time.sleep(int(seconds))
