import behave
import time
import random


@behave.given(u'I create a project by the name of "{project_name}"')
def step_impl(context, project_name):
    if hasattr(context.feature, 'dataloop_feature_project'):
        context.project = context.feature.dataloop_feature_project
    else:
        num = random.randint(10000, 100000)
        project_name = 'to-delete-test-{}_{}'.format(str(num), project_name)
        context.project = context.dl.projects.create(project_name=project_name)
        context.to_delete_projects_ids.append(context.project.id)
        context.feature.dataloop_feature_project = context.project
        time.sleep(5)

    context.project_name = context.project.name
    context.dataset_count = 0

    if 'bot.create' in context.feature.tags:
        if hasattr(context.feature, 'bot_user'):
            context.bot_user = context.feature.bot_user
        else:
            bot_name = 'test_bot_{}'.format(random.randrange(1000, 10000))
            context.bot = context.project.bots.create(name=bot_name)
            context.feature.bot = context.bot
            context.bot_user = context.bot.email
            context.feature.bot_user = context.bot_user
