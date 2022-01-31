import datetime

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
    execution_mode = None
    function_name = None

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
                execution_mode = param[1]
        elif param[0] == "function_name":
            if param[1] != "None":
                function_name = param[1]

    params_temp = {'name': name, 'filters': filters, 'resource': resource, 'actions': actions, 'active': active,
                   'execution_mode': execution_mode, 'function_name': function_name, 'service_id': context.service.id}

    params = {k: v for k, v in params_temp.items() if v is not None}

    context.trigger = context.service.triggers.create(**params)


@behave.when(u"I create a cron trigger")
def step_impl(context):
    function_name = None
    name = None

    params = context.table.headings
    for param in params:
        param = param.split("=")
        if param[0] == "name":
            if param[1] != "None":
                name = '{}-{}'.format(param[1], random.randrange(1000, 10000))
        elif param[0] == "function_name":
            if param[1] != "None":
                function_name = param[1]

    context.trigger = context.service.triggers.create(function_name=function_name,
                                                      trigger_type="Cron",
                                                      name=name,
                                                      start_at=datetime.datetime.now().isoformat(),
                                                      end_at=datetime.datetime(2024, 8, 23).isoformat(),
                                                      cron="0 5 * * *")


@behave.given(u"I create a cron trigger")
def step_impl(context):
    function_name = None
    name = None

    params = context.table.headings
    for param in params:
        param = param.split("=")
        if param[0] == "name":
            if param[1] != "None":
                name = '{}-{}'.format(param[1], random.randrange(1000, 10000))
        elif param[0] == "function_name":
            if param[1] != "None":
                function_name = param[1]

    context.trigger = context.service.triggers.create(function_name=function_name,
                                                      trigger_type="Cron",
                                                      name=name,
                                                      start_at=datetime.datetime.now().isoformat(),
                                                      end_at=datetime.datetime(2024, 8, 23).isoformat(),
                                                      cron="0 5 * * *")


@behave.then(u'I receive a Trigger entity')
def step_impl(context):
    assert isinstance(context.trigger, context.dl.entities.Trigger)


@behave.then(u'I receive a Trigger entity with function "{function_name}"')
def step_impl(context, function_name):
    assert isinstance(context.trigger, context.dl.entities.Trigger)
    assert context.trigger.function_name == function_name


@behave.then(u'Service was triggered on "{resource_type}"')
def step_impl(context, resource_type):
    context.trigger_type = resource_type
    num_try = 60
    interval = 10
    triggered = False

    for i in range(num_try):
        time.sleep(interval)
        if resource_type == 'item':
            item = context.dataset.items.get(item_id=context.uploaded_item_with_trigger.id)
            if 'executionLogs' in item.system:
                if context.service.name in item.system['executionLogs']:
                    triggered = True
                    break
        elif resource_type == 'annotation':
            item = context.annotation.item.annotations.get(annotation_id=context.annotation.id)
            if item.label == "Edited":
                triggered = True
                break
        elif resource_type == 'dataset':
            if context.service.executions.list().items_count == 1:
                execution = context.service.executions.list()[0][0]
                assert resource_type in execution.input.keys()
                triggered = True
                break
        elif resource_type == 'task':
            if context.task.name == "name updated by trigger":
                triggered = True
                break

    assert triggered


@behave.given(u'There is a package (pushed from "{package_path}") by the name of "{package_name}"')
def step_impl(context, package_name, package_path):
    package_path = os.path.join(os.environ["DATALOOP_TEST_ASSETS"], package_path)
    package_name = '{}-{}'.format(package_name, random.randrange(1000, 10000))
    context.package = context.project.packages.push(src_path=package_path, package_name=package_name)
    context.to_delete_packages_ids.append(context.package.id)
    assert isinstance(context.package, context.dl.entities.Package)


@behave.given(u'There is a package (pushed from "{package_path}") with function "{function_name}"')
def step_impl(context, function_name, package_path):
    package_path = os.path.join(os.environ["DATALOOP_TEST_ASSETS"], package_path)
    package_name = '{}-{}'.format(function_name, random.randrange(1000, 10000))

    function_io = context.dl.FunctionIO(name='item', type=context.dl.PackageInputType.ITEM)
    function = context.dl.PackageFunction(name=function_name, inputs=function_io)
    module = context.dl.PackageModule(name='default_module', functions=[function], entry_point='main.py')

    context.package = context.project.packages.push(src_path=package_path,
                                                    package_name=package_name,
                                                    modules=module)
    context.to_delete_packages_ids.append(context.package.id)
    assert isinstance(context.package, context.dl.entities.Package)


@behave.given(
    u'There is a service by the name of "{service_name}" with module name "{module_name}" saved to context "{service_attr_name}"')
def step_impl(context, service_name, module_name, service_attr_name):
    service_name = '{}-{}'.format(service_name, random.randrange(1000, 10000))
    runtime = {"gpu": False, "numReplicas": 1, 'concurrency': 1}
    setattr(context, service_attr_name, context.package.services.deploy(service_name=service_name,
                                                                        bot=context.bot_user,
                                                                        runtime=runtime,
                                                                        module_name=module_name))
    context.to_delete_services_ids.append(getattr(context, service_attr_name).id)
    assert isinstance(getattr(context, service_attr_name), context.dl.entities.Service)


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
    context.annotation = annotation.upload()
    assert isinstance(context.annotation, context.dl.entities.Annotation)
