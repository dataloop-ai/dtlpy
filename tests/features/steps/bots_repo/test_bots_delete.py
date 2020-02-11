import behave


@behave.when(u'I delete the created bot by email')
def step_impl(context):
    context.project.bots.delete(bot_email=context.bot.email)


@behave.when(u'I try to delete a bot by the name of "{bot_name}"')
def step_impl(context, bot_name):
    try:
        context.project.bots.delete(bot_email=bot_name)
        context.error = None
    except Exception as e:
        context.error = e


@behave.then(u'There are no bot by the name of "{bot_name}"')
def step_impl(context, bot_name):
    try:
        bot = context.project.bots.get(bot_name=bot_name)
    except:
        assert False, 'cant get bot'


@behave.given(u'There are no bots in project')
def step_impl(context):
    try:
        for bot in context.project.bots.list():
            bot.delete()
    except:
        assert False, 'cant delete bot'
