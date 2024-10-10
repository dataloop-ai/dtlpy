import os
import dtlpy as dl
import behave
import json
import time

from dtlpy import FunctionIO, PackageInputType, KubernetesAutoscalerType



@behave.when(u"I create a service")
def step_impl(context):
    service_name = None
    package = None
    revision = None
    config = None
    runtime = None
    execution_timeout = None
    max_attempts = None
    pod_type = None
    bot_user = context.bot_user if hasattr(context, "bot_user") else None

    params = context.table.headings
    for param in params:
        param = param.split("=")
        if param[0] == "service_name":
            if param[1] != "None":
                service_name = param[1]
        elif param[0] == "package":
            if param[1] != "None":
                package = param[1]
        elif param[0] == "revision":
            if param[1] != "None":
                revision = param[1]
        elif param[0] == "config":
            if param[1] != "None":
                config = json.loads(param[1])
        elif param[0] == "runtime":
            if param[1] != "None":
                runtime = json.loads(param[1])
            else:
                runtime = {"numReplicas": 1, 'concurrency': 1}
        elif param[0] == "execution_timeout":
            if param[1] != "None":
                execution_timeout = int(param[1])
        elif param[0] == "max_attempts":
            if param[1] != "None":
                max_attempts = int(param[1])
        elif param[0] == "pod_type":
            if param[1] != "None":
                pod_type = param[1]
        elif param[0] == "bot_user":
            if param[1] != "None":
                bot_user = context.project.bots.get(bot_name=param[1])
            else:
                bot_user = context.bot_user


    context.service = context.package.services._create(
        bot=bot_user,
        service_name=service_name,
        package=context.package,
        revision=revision,
        init_input=config,
        runtime=runtime,
        execution_timeout=execution_timeout,
        max_attempts=max_attempts,
        pod_type=pod_type
    )
    context.to_delete_services_ids.append(context.service.id)
    if hasattr(context, "first_service"):
        context.second_service = context.service
    else:
        context.first_service = context.service


@behave.when(u"I create a service with autoscaler")
def step_impl(context):
    service_name = None
    package = None
    revision = None
    config = None
    runtime = None
    pod_type = None

    params = context.table.headings
    for param in params:
        param = param.split("=")
        if param[0] == "service_name":
            if param[1] != "None":
                service_name = param[1]
        elif param[0] == "package":
            if param[1] != "None":
                package = param[1]
        elif param[0] == "revision":
            if param[1] != "None":
                revision = param[1]
        elif param[0] == "config":
            if param[1] != "None":
                config = json.loads(param[1])
        elif param[0] == "pod_type":
            if param[1] != "None":
                pod_type = param[1]
        elif param[0] == "runtime":
            if param[1] != "None":
                runtime = json.loads(param[1])
            else:
                runtime = {"gpu": False, "numReplicas": 1, 'concurrency': 1,
                           'autoscaler': {
                               'type': KubernetesAutoscalerType.RABBITMQ, 'minReplicas': 1,
                               'maxReplicas': 5,
                               'queueLength': 10}}

    context.service = context.package.services._create(
        bot=context.bot_user,
        service_name=service_name,
        package=context.package,
        revision=revision,
        init_input=config,
        runtime=runtime,
        pod_type=pod_type
    )
    context.to_delete_services_ids.append(context.service.id)
    if hasattr(context, "first_service"):
        context.second_service = context.service
    else:
        context.first_service = context.service


@behave.then(u'I upload an item by the name of "{item_name}"')
def step_impl(context, item_name):
    local_path = os.path.join(os.environ['DATALOOP_TEST_ASSETS'], '0000000162.jpg')
    context.item = context.dataset.items.upload(local_path=local_path)


@behave.then(u"I run a service execute for the item")
def step_impl(context):
    context.ex = context.service.execute(
        execution_input=FunctionIO(name='item', value=context.item.id, type=PackageInputType.ITEM),
        function_name='run',
        project_id=context.package.project_id)


@behave.then(u"I receive a Service entity")
def step_impl(context):
    assert isinstance(context.service, context.dl.entities.Service)


@behave.then(u'Log "{log_message}" is in service.log()')
def step_impl(context, log_message):
    num_tries = 60
    interval_time = 5
    success = False

    for i in range(num_tries):
        time.sleep(interval_time)
        for log in context.service.log(view=False):
            if log_message in log:
                success = True
                break
        if success:
            break

    assert success, f"TEST FAILED: After {round(num_tries * interval_time / 60, 1)} minutes"


@behave.when(u'I deploy a service from function "{service_name}"')
def step_impl(context, service_name):
    try:
        def run(self, item=None, progress=None):
            """
            Write your main package function here

            :param progress: Use this to update the progress of your package
            :return:
            """
            # these lines can be removed
            assert isinstance(progress, dl.Progress)
            progress.update(status='inProgress', progress=0)

        context.service = context.project.services.deploy(func=run,
                                                          service_name=service_name)

    except Exception as e:
        context.error = e


@behave.then(u"I call service.execute() on items in dataset")
def step_impl(context):
    items_list = [item.id for item in context.dataset.items.list().items]
    context.execution = context.service.execute(
        execution_input=FunctionIO(name='items', value=items_list, type=PackageInputType.ITEMS),
        function_name='run',
        project_id=context.package.project_id)

