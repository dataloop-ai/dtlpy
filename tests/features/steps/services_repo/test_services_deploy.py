import behave
import json


@behave.given(u'There are no services')
def step_impl(context):
    assert len(context.package.services.list()) == 0


@behave.when(u'I deploy a service')
def step_impl(context):
    service_name = None
    package = None
    revision = None
    config = None
    runtime = None

    params = context.table.headings
    for param in params:
        param = param.split('=')
        if param[0] == 'service_name':
            if param[1] != 'None':
                service_name = param[1]
        elif param[0] == 'package':
            if param[1] != 'None':
                package = param[1]
        elif param[0] == 'revision':
            if param[1] != 'None':
                revision = int(param[1])
        elif param[0] == 'config':
            if param[1] != 'None':
                config = json.loads(param[1])
        elif param[0] == 'runtime':
            if param[1] != 'None':
                runtime = json.loads(param[1])

    context.service = context.package.services.deploy(
        bot=context.bot_user,
        service_name=service_name,
        package=context.package,
        revision=revision,
        init_input=config,
        runtime=runtime
    )
    context.to_delete_services_ids.append(context.service.id)


@behave.then(u'There is only one service')
def step_impl(context):
    services_list = context.package.services.list()
    assert len(services_list) == 1
    assert services_list[0].to_json() == context.service.to_json()
