import behave
import json
import time


@behave.when(u"I create a service")
def step_impl(context):
    service_name = None
    package = None
    revision = None
    config = None
    runtime = None

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
                revision = int(param[1])
        elif param[0] == "config":
            if param[1] != "None":
                config = json.loads(param[1])
        elif param[0] == "runtime":
            if param[1] != "None":
                runtime = json.loads(param[1])
            else:
                runtime = {"gpu": False, "numReplicas": 1, 'concurrency': 1}

    context.service = context.package.services._create(
        bot=context.bot_user,
        service_name=service_name,
        package=context.package,
        revision=revision,
        init_input=config,
        runtime=runtime,
    )
    context.to_delete_services_ids.append(context.service.id)
    if hasattr(context, "first_service"):
        context.second_service = context.service
    else:
        context.first_service = context.service


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

    assert success
