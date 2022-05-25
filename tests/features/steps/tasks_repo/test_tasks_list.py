import behave
import datetime
import random


@behave.when(u'I list Tasks by param "{param}" value "{value}"')
def step_impl(context, param, value):
    kwargs = dict()
    if param == 'project_ids':
        project_ids = list()
        if value == 'current_project':
            project_ids.append(context.project.id)
        elif value == 'second_project':
            project_ids.append(context.second_project.id)
        elif value == 'both':
            project_ids.append(context.project.id)
            project_ids.append(context.second_project.id)
        kwargs['project_ids'] = project_ids
    elif param == 'recipe':
        project_ids = list()
        project_ids.append(context.project.id)
        project_ids.append(context.second_project.id)
        kwargs['project_ids'] = project_ids
        if value == 'current_project':
            for dataset in context.project.datasets.list():
                if dataset.name != 'Binaries':
                    recipe = dataset.get_recipe_ids()[0]
        elif value == 'second_project':
            for dataset in context.second_project.datasets.list():
                if dataset.name != 'Binaries':
                    recipe = dataset.get_recipe_ids()[0]
        else:
            raise Exception('Unknown type of recipe value')
        kwargs['recipe'] = recipe
    elif param == 'creator':
        project_ids = list()
        project_ids.append(context.project.id)
        project_ids.append(context.second_project.id)
        kwargs['project_ids'] = project_ids
        kwargs['creator'] = context.dl.info()['user_email']
    elif param in ['min_date', 'max_date']:
        project_ids = list()
        project_ids.append(context.project.id)
        project_ids.append(context.second_project.id)
        kwargs['project_ids'] = project_ids
        if value == '2_days_from_now':
            value = (datetime.datetime.today().timestamp() + (2 * 24 * 60 * 60)) * 1000
        elif value == '2_weeks_from_now':
            value = (datetime.datetime.today().timestamp() + (2 * 7 * 24 * 60 * 60)) * 1000
        elif value == 'today':
            value = (datetime.datetime.today().timestamp() + (60 * 60)) * 1000
        kwargs[param] = value
    else:
        kwargs[param] = value

    context.tasks_list = context.project.tasks.list(**kwargs)
    print(kwargs)


@behave.then(u'I receive a list of "{count}" tasks')
def step_impl(context, count):
    success = len(context.tasks_list) == int(count)
    for task in context.tasks_list:
        success = success and isinstance(task, context.dl.entities.Task)
    if not success:
        print(context.tasks_list)
        print(context.project.tasks.list())
    assert success


@behave.given(u'There is a second project and dataset')
def step_impl(context):
    context.second_project = context.dl.projects.create(
        '{}-second-project-tasks-list'.format(random.randrange(100, 1000000)))
    context.second_dataset = context.second_project.datasets.create(
        'second_dataset_{}'.format(random.randrange(100, 1000000)))
