# coding=utf-8
"""Bots repository get service testing."""

import behave


@behave.when(u'I get a bot by the name of "{bot_name}"')
def step_impl(context, bot_name):
    context.bot_get = context.project.bots.get(bot_name=bot_name)


@behave.then(u'Received bot equals created bot')
def step_impl(context):
    assert context.bot_get.to_json() == context.bot.to_json()
