import time
import behave
import json


@behave.then(u"Service attributes are modified")
def step_impl(context):
    revision = None
    config = None
    runtime = None

    params = context.table.headings
    for param in params:
        param = param.split("=")
        if param[0] == "revision":
            if param[1] != "None":
                revision = int(param[1])
        elif param[0] == "config":
            if param[1] != "None":
                config = json.loads(param[1])
        elif param[0] == "runtime":
            if param[1] != "None":
                runtime = json.loads(param[1])

    assert context.trigger_update.revision == revision
    assert context.trigger_update.config == config
    assert context.trigger_update.runtime == runtime


@behave.then(u"I receive an updated Service object")
def step_impl(context):
    assert isinstance(context.service_update, context.dl.entities.Service)


@behave.when(u'I change service "{attribute}" to "{value}"')
def step_impl(context, attribute, value):
    if attribute in ['gpu', 'image']:
        context.service.runtime[attribute] = value
    elif attribute in ['numReplicas', 'concurrency']:
        setattr(context.service.runtime, attribute, int(value))
    elif attribute in ['config']:
        context.service.config = json.loads(value)
    elif attribute in ['packageRevision']:
        setattr(context.service, attribute, int(value))
    else:
        setattr(context.service, attribute, value)


@behave.when(u'I update service')
def step_impl(context):
    context.service_update = context.service.update()


@behave.then(u'Service received equals service changed except for "{updated_attribute}"')
def step_impl(context, updated_attribute):
    updated_to_json = context.service_update.to_json()
    origin_to_json = context.service.to_json()
    if 'runtime' in updated_attribute:
        attribute = updated_attribute.split('.')[-1]
        updated_to_json['runtime'].pop(attribute, None)
        origin_to_json['runtime'].pop(attribute, None)
    else:
        updated_to_json.pop(updated_attribute, None)
        origin_to_json.pop(updated_attribute, None)

    updated_to_json.pop('updatedAt', None)
    origin_to_json.pop('updatedAt', None)

    updated_to_json.pop('version', None)
    origin_to_json.pop('version', None)

    updated_to_json.pop('revisions', None)
    origin_to_json.pop('revisions', None)

    assert len(context.service_update.revisions) == len(context.service_revisions) + 1
    assert updated_to_json == origin_to_json


@behave.given(u'I execute service')
def step_impl(context):
    context.execution = context.service.execute(project_id=context.service.project_id)


@behave.given(u'Service has max_attempts of "{max_attempts}"')
def step_impl(context, max_attempts):
    max_attempts = int(max_attempts)
    assert context.service.max_attempts == max_attempts


@behave.given(u'Execution is running')
def step_impl(context):
    interval = 10
    num_tries = 30
    success = False
    for i in range(num_tries):
        time.sleep(interval)
        if success:
            break
        e = context.execution = context.service.executions.get(execution_id=context.execution.id)
        success = e.latest_status['status'] in ['in-progress', 'inProgress']
    assert success, f"TEST FAILED: latest status - {e.latest_status['status']}, After {round(num_tries * interval / 60, 1)} minutes"


@behave.when(u'I update service with force="{force}"')
def step_impl(context, force: str):
    force = bool(force)
    context.service = context.service.update(force=force)


@behave.then(u'Execution stopped immediately')
def step_impl(context):
    interval = 10
    num_tries = 24
    success = False
    for i in range(num_tries):
        time.sleep(interval)
        if success:
            break
        e = context.execution = context.service.executions.get(execution_id=context.execution.id)
        success = e.latest_status['status'] == 'failed'
    assert success, f"TEST FAILED: After {round(num_tries * interval / 60, 1)} minutes"


@behave.when(u'I get service revisions')
def step_impl(context):
    context.service_revisions = context.service.revisions


@behave.when(u'I update service to latest package revision')
def step_impl(context):
    context.package = context.project.packages.get(package_id=context.service.package_id)
    context.service.package_revision = context.package.version
    context.service = context.service.update(True)
