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
    try:
        context.trigger = context.service.triggers.create(**params)
        context.error = None
    except Exception as e:
        context.error = e


@behave.when(u"I create a cron trigger")
def step_impl(context):
    function_name = None
    name = None
    cron = None

    params = context.table.headings
    for param in params:
        param = param.split("=")
        if param[0] == "name":
            if param[1] != "None":
                name = '{}-{}'.format(param[1], random.randrange(1000, 10000))
        elif param[0] == "function_name":
            if param[1] != "None":
                function_name = param[1]
        elif param[0] == "cron":
            if param[1] != "None":
                cron = param[1]
            else:
                cron = "0 5 * * *"

    context.trigger = context.service.triggers.create(function_name=function_name,
                                                      trigger_type="Cron",
                                                      name=name,
                                                      start_at=datetime.datetime.now().isoformat(),
                                                      end_at=datetime.datetime(2024, 8, 23).isoformat(),
                                                      cron=cron)


@behave.given(u"I create a cron trigger")
def step_impl(context):
    function_name = None
    name = None
    cron = None

    params = context.table.headings
    for param in params:
        param = param.split("=")
        if param[0] == "name":
            if param[1] != "None":
                name = '{}-{}'.format(param[1], random.randrange(1000, 10000))
        elif param[0] == "function_name":
            if param[1] != "None":
                function_name = param[1]
        elif param[0] == "cron":
            if param[1] != "None":
                cron = param[1]
            else:
                cron = "* 5 * * *"

    context.trigger = context.service.triggers.create(function_name=function_name,
                                                      trigger_type="Cron",
                                                      name=name,
                                                      start_at=datetime.datetime.now().isoformat(),
                                                      cron=cron)


@behave.then(u'I receive a Trigger entity')
def step_impl(context):
    assert isinstance(context.trigger, context.dl.entities.Trigger)


@behave.then(u'I receive a CronTrigger entity')
def step_impl(context):
    assert isinstance(context.trigger, context.dl.entities.CronTrigger)


@behave.when(u'I set the trigger in the context')
def step_impl(context):
    composition = context.project.compositions.get(composition_id=context.app.composition_id)
    context.trigger = context.project.triggers.get(trigger_id=composition["triggers"][0]["triggerId"])
    context.service = context.trigger.service


@behave.when(u'I set the execution in the context')
def step_impl(context):
    num_try = 6
    interval = 2
    for i in range(num_try):
        time.sleep(interval)
        if context.service.executions.list().items_count > 0:
            context.execution = context.service.executions.list().items[0]
            break


@behave.when(u'I set code path "{path}" to context')
def step_impl(context, path):
    context.codebase_local_dir = os.path.join(os.environ['DATALOOP_TEST_ASSETS'], path)


@behave.then(u'I receive a Trigger entity with function "{function_name}"')
def step_impl(context, function_name):
    assert isinstance(context.trigger, context.dl.entities.Trigger)
    assert context.trigger.function_name == function_name


@behave.then(u'Service was triggered on "{resource_type}"')
def step_impl(context, resource_type):
    context.trigger_type = resource_type
    num_try = 36
    interval = 5
    triggered = False

    for i in range(num_try):
        time.sleep(interval)
        if resource_type == 'item':
            filters = context.dl.Filters(resource=context.dl.FiltersResource.EXECUTION)
            filters.add(field='serviceId', values=context.service.id)
            filters.add(field='resources.id', values=context.uploaded_item_with_trigger.id)
            execution_page = context.service.executions.list(filters=filters)
            if execution_page.items_count == 1:
                triggered = True
                break
        elif resource_type == 'itemclone':
            filters = context.dl.Filters(resource=context.dl.FiltersResource.EXECUTION)
            filters.add(field='serviceId', values=context.service.id)
            filters.add(field='resources.id', values=context.uploaded_item_with_trigger.id)
            execution_page = context.service.executions.list(filters=filters)
            if execution_page.items_count > 0:
                triggered = True
                break
        elif resource_type == 'annotation':
            annotation = context.annotation.item.annotations.get(annotation_id=context.annotation.id)
            if annotation.label == "Edited":
                triggered = True
                break
        elif resource_type == 'dataset':
            if context.service.executions.list().items_count == 1:
                execution = context.service.executions.list()[0][0]
                assert resource_type in execution.input.keys()
                triggered = True
                break
        elif resource_type == 'task':
            context.task = context.project.tasks.get(task_id=context.task.id)
            if context.task.name == "name updated by trigger":
                triggered = True
                break
        elif resource_type == 'assignment':
            context.assignment = context.project.assignments.get(assignment_id=context.assignment.id)
            if "name-updated" in context.assignment.name:
                triggered = True
                break
        elif resource_type == 'hidden-item':
            item = context.dataset.items.get(item_id=context.uploaded_item_with_trigger.id)
            if len(item.resource_executions.list()) > 0 and item.resource_executions.list()[0][0].service_name == context.service.name:
                triggered = True
                break
        elif resource_type == 'string':
            execution = None
            pages = context.service.executions.list()
            executions = pages.items
            if len(executions) > 0:
                execution = executions[0]
            if execution is not None and len(execution.input) > 0:
                context.execution = context.service.executions.list()[0][0]
                triggered = True
                break
        context.dl.logger.debug("Step is running for {:.2f}[s] and now Going to sleep {:.2f}[s]".format((i + 1) * interval,
                                                                                                        interval))

    assert triggered, f"TEST FAILED: After {round(num_try * interval / 60, 1)} minutes"


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

    function_io = [context.dl.FunctionIO(name='item', type=context.dl.PackageInputType.ITEM)]
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
    runtime = context.dl.KubernetesRuntime(autoscaler=context.dl.KubernetesAutoscaler(min_replicas=1)).to_json()
    setattr(context, service_attr_name, context.package.services.deploy(service_name=service_name,
                                                                        bot=context.bot_user,
                                                                        runtime=runtime,
                                                                        module_name=module_name))
    context.to_delete_services_ids.append(getattr(context, service_attr_name).id)
    assert isinstance(getattr(context, service_attr_name), context.dl.entities.Service)


@behave.given(
    u'There is a service with max_attempts of "{max_attempts}" by the name of "{service_name}" with module name "{module_name}" saved to context "{service_attr_name}"')
def step_impl(context, service_name, module_name, service_attr_name, max_attempts):
    max_attempts = int(max_attempts)
    service_name = '{}-{}'.format(service_name, random.randrange(1000, 10000))
    runtime = {"gpu": False, "numReplicas": 1, 'concurrency': 1}
    setattr(
        context, service_attr_name, context.package.services.deploy(
            service_name=service_name,
            bot=context.bot_user,
            runtime=runtime,
            module_name=module_name,
            max_attempts=max_attempts
        )
    )
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
    if hasattr(context, 'uploaded_item_with_trigger'):
        annotation = context.dl.Annotation.new(annotation_definition=context.dl.Point(y=200, x=200, label='dog'),
                                               item=context.uploaded_item_with_trigger)
    else:
        annotation = context.dl.Annotation.new(annotation_definition=context.dl.Point(y=200, x=200, label='dog'),
                                               item=context.item)
    context.annotation = annotation.upload()
    assert isinstance(context.annotation, context.dl.entities.Annotation)
