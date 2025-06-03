import behave


@behave.then(u'I validate app.custom_installation is equal to composition')
def step_impl(context):
    context.app = context.project.apps.get(app_name=context.app.name)
    app_composition = context.project.compositions.get(context.app.composition_id)

    app_services_names = [service.get('name') for service in
                          context.app.custom_installation.get('components').get('services')]
    comp_services_names = [comp.get('name') for comp in app_composition.get('spec')]
    app_triggers_names = [service.get('name') for service in
                          context.app.custom_installation.get('components').get('triggers')]
    comp_triggers_names = [comp.get('name') for comp in app_composition.get('triggers')]
    assert app_services_names == comp_services_names, f"TEST FAILED: app_services_names is {app_services_names} composition_services_names is {comp_services_names}"
    assert app_triggers_names == comp_triggers_names, f"TEST FAILED: app_triggers_names is {app_triggers_names} composition_triggers_names is {comp_triggers_names}"


@behave.then(u'services should be updated')
def step_impl(context):
    services = context.project.services.list()
    for page in services:
        for service in page:
            if service.name.endswith('sdk'):
                assert service.version == '1.0.0', f"TEST FAILED: add new service"
            else:
                assert service.version == '1.0.1', f"TEST FAILED: update services, service version is {service.version}"


@behave.then(u'I expect app dpk version to be "{dpk_version}"')
def step_impl(context, dpk_version):
    context.app = context.project.apps.get(app_name=context.app.name)
    assert context.app.dpk_version == dpk_version, f"TEST FAILED: dpk version is {context.app.dpk_version}"


@behave.then(u'I expect app to be in status "{status}"')
def step_impl(context, status):
    context.app = context.project.apps.get(app_name=context.app.name)
    assert context.app.status == status, f"TEST FAILED: app status is {context.app.status}"
