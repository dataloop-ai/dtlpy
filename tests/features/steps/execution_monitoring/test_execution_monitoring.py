import behave
import json
import time
import os


@behave.when(u'I push and deploy package with param "{on_reset}" in "{package_directory_path}"')
def step_impl(context, package_directory_path, on_reset):
    package_directory_path = os.path.join(os.environ['DATALOOP_TEST_ASSETS'], package_directory_path)
    package_json_path = os.path.join(package_directory_path, 'package.json')

    with open(package_json_path, 'r') as f:
        package_json = json.load(f)

    if on_reset == 'None':
        package_json['services'][0].pop('onReset', None)
    else:
        package_json['services'][0]['onReset'] = on_reset

    with open(package_json_path, 'w') as f:
        json.dump(package_json, f)

    services, context.package = context.project.packages.deploy_from_file(project=context.project,
                                                                          json_filepath=package_json_path)

    context.service = services[0]
    context.to_delete_packages_ids.append(context.package.id)
    context.to_delete_services_ids.append(context.service.id)


@behave.when(u'I execute')
def step_impl(context):
    context.execution = context.service.execute(project_id=context.project.id)


@behave.when(u'I terminate execution')
def step_impl(context):
    context.execution.terminate()


@behave.then(u'Execution was terminated with error message "{message}"')
def step_impl(context, message):
    num_tries = 60
    interval = 7
    terminated = False

    for i in range(num_tries):
        time.sleep(interval)
        execution = context.service.executions.get(execution_id=context.execution.id)
        terminated = execution.to_terminate
        terminated = terminated and execution.latest_status['status'] == 'failed'
        terminated = terminated and message in execution.latest_status['message']
        if terminated:
            break

    assert terminated


@behave.then(u'Execution "{on_reset}" on timeout')
def step_impl(context, on_reset):
    time.sleep(context.service.execution_timeout + context.service.drain_time + 5)
    num_tries = 60
    interval = 7

    reset = False
    for _ in range(num_tries):
        execution = context.service.executions.get(execution_id=context.execution.id)
        for stat in execution.status:
            if on_reset == 'rerun' \
                    and stat['status'] == 'rerun' \
                    and 'Rerun due to runner timeout' in stat['message']:
                reset = True
            elif on_reset == 'failed' \
                    and stat['status'] == 'failed' \
                    and 'Failed due to runner timeout' in stat['message']:
                reset = True
            if reset:
                break
        if reset:
            break
        time.sleep(interval)

    assert reset
