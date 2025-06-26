import string
import time
import random
from multiprocessing.pool import ThreadPool

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
        if value in ['True', 'False']:
            value = eval(value)
        setattr(context.service, attribute, value)


@behave.when(u'I update service')
def step_impl(context):
    try:
        context.service_update = context.service.update()
        context.error = None
    except Exception as e:
        context.error = e


@behave.then(u'Service received equals service changed except for "{updated_attribute}"')
def step_impl(context, updated_attribute):
    if not hasattr(context, "service_update"):
        raise context.error
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

    updated_to_json.pop('updatedBy', None)
    origin_to_json.pop('updatedBy', None)

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


@behave.then(u'"{resource}" has updatedBy field')
def step_impl(context, resource: str):
    resource = getattr(context, resource)
    assert resource.updated_by is not None
    assert resource.updated_by == context.dl.info()['user_email']


def random_5_chars():
    return ''.join(random.choices(string.ascii_lowercase + string.digits, k=5)) + 'a'


long_timeout = 60 * 60 * 5


@behave.given(u'I have a paused "{service_type}" service with concurrency "{concurrency}"')
def step_impl(context, service_type: str, concurrency: str):
    concurrency = int(concurrency)

    service_name = f'{service_type}-service-{random_5_chars()}'

    def run(item):
        import time
        time.sleep(.5)
        return item

    context.service = context.project.services.deploy(
        func=run,
        service_name=service_name,
        execution_timeout=900 if service_type == 'short-term' else long_timeout,
        runtime=context.dl.KubernetesRuntime(
            concurrency=concurrency,
            autoscaler=context.dl.KubernetesRabbitmqAutoscaler(
                min_replicas=0,
                max_replicas=1
            )
        )
    )
    context.service.pause()
    context.service = context.dl.services.get(service_id=context.service.id)


@behave.given(u'I run "{num_executions}" executions and activate the service')
def step_impl(context, num_executions: str):
    num_executions = int(num_executions)
    item_id = context.dataset.items.list().items[0].id
    pool = ThreadPool(processes=10)
    for _ in range(num_executions):
        pool.apply_async(
            context.service.execute,
            kwds={'item_id': item_id, 'project_id': context.project.id}
        )

    pool.close()
    pool.join()
    context.service.resume()
    context.service = context.dl.services.get(service_id=context.service.id)


def create_filter(c):
    f = c.dl.Filters(resource=c.dl.FiltersResource.EXECUTION)
    f.add(field='serviceId', values=c.service.id)
    return f


@behave.when(u'I update the service back and forth "{num_times}" times from long-term to short-term')
def step_impl(context, num_times: str):
    num_times = int(num_times)
    context.machine_count = num_times + 1
    last_count = 0
    interval = 1

    def is_long_term(service: context.dl.Service):
        return service.execution_timeout == long_timeout

    def wait_for_some_executions_to_run(last_running_executions_count):
        max_wait = 60 * 3
        start_time = time.time()
        f = create_filter(c=context)
        f.add(
            field='latestStatus.status', values=context.dl.ExecutionStatus.SUCCESS,
            operator=context.dl.FiltersOperations.EQUAL
        )
        es = context.service.executions.list(filters=f)
        while es.items_count <= last_running_executions_count and time.time() - start_time < max_wait:
            es = context.service.executions.list(filters=f)
            time.sleep(interval)

    for _ in range(num_times):
        wait_for_some_executions_to_run(last_running_executions_count=last_count)
        if is_long_term(context.service):
            context.service.execution_timeout = timeout = 900
        else:
            context.service.execution_timeout = timeout = long_timeout
        context.service = context.service.update()
        context.service = context.dl.services.get(service_id=context.service.id)
        assert context.service.execution_timeout == timeout
        time.sleep(interval)
        filters = create_filter(c=context)
        filters.add(
            field='latestStatus.status', values=context.dl.ExecutionStatus.SUCCESS,
            operator=context.dl.FiltersOperations.EQUAL
        )
        executions = context.service.executions.list(filters=filters)
        last_count = executions.items_count


@behave.when(u'I expect all executions to be successful and no execution should have ran twice')
def step_impl(context):
    # all success
    max_wait = 60 * 10
    start_time = time.time()
    interval = 3

    while time.time() - start_time < max_wait:
        filters = create_filter(c=context)
        filters.add(
            field='latestStatus.status', values=context.dl.ExecutionStatus.SUCCESS,
            operator=context.dl.FiltersOperations.NOT_EQUAL
        )
        executions = context.service.executions.list(filters=filters)
        if len(executions.items) == 0:
            break
        else:
            print(f'Waiting for {executions.items_count} executions to finish')
        time.sleep(interval)

    # all ran once
    machines = set()
    filters = create_filter(c=context)
    pages = context.service.executions.list(filters=filters)
    statuses = [
        context.dl.ExecutionStatus.CREATED,
        'in-progress',
        context.dl.ExecutionStatus.SUCCESS
    ]
    statuses.sort()
    pattern = '-'.join(statuses)
    for page in pages:
        for execution in page:
            replica_id = execution.latest_status.get('replicaId', None)
            latest_status = execution.latest_status.get('status', None)
            if replica_id is not None:
                machines.add(replica_id)
            else:
                assert False, 'Execution status is missing replicaId'
            if latest_status != context.dl.ExecutionStatus.SUCCESS:
                print(f"Execution not successful. URL: {execution.url}")
                context.dl.logger.error(execution.url)
            assert latest_status == context.dl.ExecutionStatus.SUCCESS, f"TEST FAILED: Execution status Expected {context.dl.ExecutionStatus.SUCCESS}, Actual {latest_status}"
            e_status_list = [s['status'] for s in execution.status]
            e_status_list.sort()
            status_list = '-'.join(e_status_list)
            assert status_list == pattern, f"TEST FAILED: Execution Expected pattern {pattern}, Actual {status_list}"

    # make sure executions ran on different machines
    assert len(machines) == context.machine_count, f"TEST FAILED: Execution machine count Expected {context.machine_count} , Actual {len(machines)}"

