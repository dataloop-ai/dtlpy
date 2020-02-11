# coding=utf-8
"""Bots repository list service testing."""

import behave


@behave.when(u'I list bots in project')
def creating_a_project(context):
    context.list = context.project.bots.list()


@behave.then(u'a bot with name "{bot_name}" exists in bots list')
def step_impl(context, bot_name):
    found = False
    for bot in context.list:
        if bot_name == bot.name:
            found = True
    assert found


@behave.then(u'I receive a bots list of "{list_length}"')
def step_impl(context, list_length):
    assert len(context.list) == int(list_length)
