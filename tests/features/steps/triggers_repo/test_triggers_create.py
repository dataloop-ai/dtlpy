import behave
import time
import os
import random


@behave.when(u"I create a trigger")
def step_impl(context):
    name = None
    filters = None
    resource = None
    actions = None
    active = None
    executionMode = None

    params = context.table.headings
    for param in params:
        param = param.split("=")
        if param[0] == "name":
            if param[1] != "None":
                name = '{}-{}'.format(param[1], random.randrange(1000, 10000))
        elif param[0] == "filters":
            if param[1] != "None":
                filters = context.filters
        elif param[0] == "resource":
            if param[1] != "None":
                resource = param[1]
        elif param[0] == "action":
            if param[1] != "None":
                actions = param[1]
        elif param[0] == "active":
            active = param[1] == "True"
        elif param[0] == "executionMode":
            if param[1] != "None":
                executionMode = param[1]

    context.trigger = context.deployment.triggers.create(
        deployment_id=context.deployment.id,
        name=name,
        filters=filters,
        resource=resource,
        actions=actions,
        active=active,
        executionMode=executionMode,
    )


@behave.then(u"I receive a Trigger entity")
def step_impl(context):
    assert isinstance(context.trigger, context.dl.entities.Trigger)


@behave.then(u'Deployment was triggered on "{item_type}"')
def step_impl(context, item_type):
    is_item = item_type == 'item'
    if is_item:
        item = context.uploaded_item_with_trigger
    else:
        item = context.annotation
    num_try = 10
    triggered = False

    for i in range(num_try):
        time.sleep(5)
        if is_item:
            item = context.dataset.items.get(item_id=item.id)
            if 'plugins' in item.system:
                if context.plugin.name in item.system['plugins']:
                    triggered = True
                    break
        else:
            item = item.update()
            if item.label == "Edited":
                triggered = True
                break

    assert triggered


@behave.given(
    u'There is a plugin (pushed from "{plugin_path}") by the name of "{plugin_name}"'
)
def step_impl(context, plugin_name, plugin_path):
    plugin_path = os.path.join(os.environ["DATALOOP_TEST_ASSETS"], plugin_path)
    plugin_name = '{}_{}'.format(plugin_name, random.randrange(1000, 10000))
    context.plugin = context.project.plugins.push(src_path=plugin_path, plugin_name=plugin_name)
    assert isinstance(context.plugin, context.dl.entities.Plugin)


@behave.given(u'There is a deployment by the name of "{deployment_name}"')
def step_impl(context, deployment_name):
    deployment_name = '{}-{}'.format(deployment_name, random.randrange(1000, 10000))
    context.deployment = context.plugin.deployments.deploy(deployment_name=deployment_name)
    assert isinstance(context.deployment, context.dl.entities.Deployment)


@behave.when(u"I edit item user metadata")
def step_impl(context):
    time.sleep(3)
    if 'user' not in context.uploaded_item_with_trigger.metadata:
        context.uploaded_item_with_trigger.metadata['user'] = dict()
    context.uploaded_item_with_trigger.metadata['user']['edited'] = True
    context.uploaded_item_with_trigger.update()


@behave.when(u"I annotate item")
def step_impl(context):
    time.sleep(3)
    annotation = context.dl.Annotation.new(annotation_definition=context.dl.Point(y=200, x=200, label='dog'),
                                           item=context.uploaded_item_with_trigger)
    annotations = annotation.upload()
    assert len(annotations) == 1
    context.annotation = annotations[0]
    assert isinstance(context.annotation, context.dl.entities.Annotation)
