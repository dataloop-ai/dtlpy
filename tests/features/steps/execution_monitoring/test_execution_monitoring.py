import behave
import json
import time
import os


@behave.when(u'I push and deploy package with param "{on_reset}" in "{package_directory_path}"')
def step_impl(context, package_directory_path, on_reset):
    package_directory_path = os.path.join(os.environ['DATALOOP_TEST_ASSETS'], package_directory_path)
    service_json_path = os.path.join(package_directory_path, 'service.json')

    with open(service_json_path, 'r') as f:
        service_json = json.load(f)

    if on_reset == 'None':
        service_json.pop('on_reset', None)
    else:
        service_json['on_reset'] = on_reset

    with open(service_json_path, 'w') as f:
        json.dump(service_json, f)

    context.package = context.project.packages.push(src_path=package_directory_path)
    context.to_delete_packages_ids.append(context.package.id)
    context.service = context.project.services.deploy_from_local_folder(bot=context.bot_user,
                                                                        cwd=package_directory_path)

    context.to_delete_services_ids.append(context.service.id)


@behave.when(u'I execute')
def step_impl(context):
    context.execution = context.service.execute(project_id=context.project.id)


@behave.when(u'I terminate execution')
def step_impl(context):
    context.execution.terminate()


@behave.then(u'Execution was terminated')
def step_impl(context):
    num_tries = 10
    interval = 10
    terminated = False

    for i in range(num_tries):
        time.sleep(interval)
        execution = context.service.executions.get(execution_id=context.execution.id)
        terminated = execution.to_terminate
        terminated = terminated and execution.latest_status['status'] == 'failed'
        terminated = terminated and 'InterruptedError' in execution.latest_status['message']
        if terminated:
            break

    assert terminated


@behave.then(u'Execution "{on_reset}" on timeout')
def step_impl(context, on_reset):
    time.sleep(context.service.execution_timeout + context.service.drain_time + 5)
    num_tries = 10
    interval = 3

    reset = False
    for _ in range(num_tries):
        execution = context.service.executions.get(execution_id=context.execution.id)
        for stat in execution.status:
            if on_reset == 'rerun' \
                    and stat['status'] == 'created' \
                    and 'Return to queue due to runner timeout' in stat['message'] \
                    and execution.attempts > 1:
                reset = True
            elif on_reset == 'failed' \
                    and stat['status'] == 'failed' \
                    and 'Failed due to runner timeout' in stat['message']:
                reset = True
        if reset:
            break
        time.sleep(interval)

    assert  reset
