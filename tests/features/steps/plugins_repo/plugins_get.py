import behave
import os


@behave.when(u'I get plugin by the name of "{plugin_name}"')
def step_impl(context, plugin_name):
    context.plugin_get = context.project.plugins.get(plugin_name=plugin_name)


@behave.when(u'I get plugin by id')
def step_impl(context):
    context.plugin_get = context.project.plugins.get(plugin_id=context.plugin.id)


@behave.then(u'I get a plugin entity')
def step_impl(context):
    assert 'Plugin' in str(type(context.plugin_get))


@behave.then(u'It is equal to plugin created')
def step_impl(context):
    assert context.plugin.to_json() == context.plugin_get.to_json()
