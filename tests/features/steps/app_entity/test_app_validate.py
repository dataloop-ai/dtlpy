import behave
import dictdiffer


@behave.then(u'I validate app.custom_installation is equal to composition')
def step_impl(context):
    context.app = context.project.apps.get(app_name=context.app.name)
    app_composition = context.project.compositions.get(context.app.composition_id)

    app_services_names = [service.get('name') for service in context.app.custom_installation.get('components').get('services')]
    comp_services_names = [comp.get('name') for comp in app_composition.get('spec')]
    app_triggers_names = [service.get('name') for service in context.app.custom_installation.get('components').get('triggers')]
    comp_triggers_names = [comp.get('name') for comp in app_composition.get('triggers')]
    assert app_services_names == comp_services_names, f"TEST FAILED: app_services_names is {app_services_names} composition_services_names is {comp_services_names}"
    assert app_triggers_names == comp_triggers_names, f"TEST FAILED: app_triggers_names is {app_triggers_names} composition_triggers_names is {comp_triggers_names}"

