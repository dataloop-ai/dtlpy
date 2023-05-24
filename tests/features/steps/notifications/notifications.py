import time
import behave
import dtlpy as dl


@behave.given(u'Service has wrong docker image')
def step_impl(context):
    context.service.runtime.runner_image = 'randomassimagenamenoonewillneveruse19'
    context.service = context.service.update(force=True)


@behave.then(u'I receive "{error}" notification')
def step_impl(context, error: str):
    success = False
    timeout = 7 * 60 * 1000
    start = time.time()
    while time.time() - start < timeout:
        messages = dl.messages._list(context={'project': context.project.id})
        if len(messages) > 0:
            ms = [m for m in messages if error in m.notification_code and m.resource_id == context.service.id]
            if len(ms) > 0:
                success = True
                break
        time.sleep(5)

    assert success, 'No notification received'


@behave.then(u'Service is deactivated by system')
def step_impl(context):
    timeout = 7 * 60 * 1000
    start = time.time()
    while time.time() - start < timeout:
        context.service = context.project.services.get(service_id=context.service.id)
        if context.service.active is False:
            break
        time.sleep(5)

    assert context.service.active is False


@behave.given(u'I delete service code base')
def step_impl(context):
    dataset = context.project.datasets.get(dataset_name='Binaries')
    for item in dataset.items.list().all():
        item.delete()


@behave.given(u'I add bad requirements to service')
def step_impl(context):
    context.package.requirements = [
        dl.PackageRequirement(name='nofuckingwaysucharequirementexist1723', version='1.0.0')
    ]
    context.package = context.package.update()
    context.service.package_revision = context.package.version
    context.service = context.service.update()

