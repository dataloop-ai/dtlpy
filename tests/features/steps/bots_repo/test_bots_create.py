import behave


@behave.when(u'I try to create a bot by the name of "{bot_name}"')
def creating_a_project(context, bot_name):
    try:
        context.bot = context.project.bots.create(name=bot_name)
        context.error = None
    except Exception as e:
        context.error = e


@behave.when(u'I create a bot by the name of "{bot_name}"')
def creating_a_project(context, bot_name):
    context.bot = context.project.bots.create(name=bot_name)
    context.bot_user = context.bot

@behave.then(u'Bot object by the name of "{bot_name}" should be created')
def project_object_should_be_created(context, bot_name):
    assert type(context.project) == context.dl.entities.Project
    assert context.project.name == context.project_name
