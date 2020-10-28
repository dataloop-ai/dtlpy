import behave
import time
import random


@behave.given(u'I create projects by the name of "{projects_name}"')
def step_impl(context, projects_name):
    projects_name = list(projects_name.split(' '))
    context.projects = list()
    context.projects_name = list()

    for project_name in projects_name:
        if project_name != '':
            num = random.randint(10000, 100000)
            project_name = 'to-delete-test-{}_{}'.format(str(num), project_name)
            context.projects_name.append(project_name)
            context.projects.append(context.dl.projects.create(project_name=project_name))

    time.sleep(5)  # to sleep because authorization takes time
    context.dataset_count = 0

    if 'bot.create' in context.feature.tags:
        bot_name = 'test_bot_{}'.format(random.randrange(1000, 10000))
        context.bot = context.projects[0].bots.create(name=bot_name)
        context.feature.bot = context.bot
        context.bot_user = context.bot.email
        context.feature.bot_user = context.bot_user


@behave.given(u'I create datasets by the name of "{datasets_name}"')
def step_impl(context, datasets_name):
    datasets_name = list(datasets_name.split(" "))
    context.datasets = list()
    context.datasets_name = list()
    i = 0
    for dataset_name in datasets_name:
        if datasets_name != '':
            context.datasets_name.append(dataset_name)
            context.datasets.append(context.projects[i].datasets.create(dataset_name=dataset_name))
            i += 1


@behave.when(u'I checkout project number {project_index}')
def step_impl(context, project_index):
    context.projects[int(project_index) - 1].checkout()


@behave.when(u'I get a dataset number {dataset_index} from checkout project')
def step_impl(context, dataset_index):
    context.dataset = \
        context.dl.datasets.get(dataset_id=context.datasets[int(dataset_index)-1].id)


@behave.when(u'I get a dataset number {dataset_index} from project number {project_index}')
def step_impl(context, dataset_index, project_index):
    context.dataset = \
        context.projects[int(project_index)-1].datasets.get(dataset_id=context.datasets[int(dataset_index)-1].id)


@behave.then(u'dataset Project_id is equal to project {project_index} id')
def step_impl(context, project_index):
    assert context.dataset.project_id == context.projects[int(project_index)-1].id


@behave.then(u'dataset Project.id is equal to project {project_index} id')
def step_impl(context, project_index):
    assert context.dataset.project.id == context.projects[int(project_index)-1].id
