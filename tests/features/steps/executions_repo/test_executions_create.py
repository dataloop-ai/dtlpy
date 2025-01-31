import string
import behave
import time
import os
import random


@behave.when(u'I create an execution with "{input_type}"')
def step_impl(context, input_type):
    time.sleep(5)
    sync = None
    inputs = list()
    with_input_entity = False
    project_id = None

    if input_type != 'None':
        with_input_entity = True

    params = context.table.headings
    for param in params:
        param = param.split("=")
        if param[0] == "sync":
            sync = param[1] == "True"
        if param[0] == "inputs":
            inputs = param[1].split(',')

    if with_input_entity:
        execution_inputs = list()

        for resource in inputs:
            if resource == 'Item':
                execution_inputs.append(
                    context.dl.FunctionIO(
                        type=resource,
                        value={
                            'item_id': context.item.id,
                            'dataset_id': context.dataset.id
                        },
                        name='item')
                )
            elif resource == 'Annotation':
                execution_inputs.append(
                    context.dl.FunctionIO(
                        type=resource,
                        value={
                            'item_id': context.item.id,
                            'dataset_id': context.dataset.id,
                            'annotation_id': context.annotation.id
                        },
                        name='annotation')
                )
            elif resource == 'Dataset':
                execution_inputs.append(
                    context.dl.FunctionIO(
                        type=resource,
                        value={
                            'dataset_id': context.dataset.id
                        },
                        name='dataset')
                )
            elif resource == 'Json':
                execution_inputs.append(
                    context.dl.FunctionIO(
                        type=resource,
                        value=context.execution_json_input,
                        name='config')
                )
            elif resource == 'e28':
                project_id = context.project.id
                context.item_id = "6500397081943346e28"
                sync = False
                execution_inputs.append(
                    context.dl.FunctionIO(
                        type=context.dl.PackageInputType.ITEMS,
                        value=[context.item_id],
                        name='items')
                )

        context.execution = context.service.executions.create(
            service_id=context.service.id,
            sync=sync,
            execution_input=execution_inputs,
            timeout=600,
            project_id=project_id
        )
    else:
        if inputs:
            resource = inputs[0]
        else:
            resource = 'no_input'

        if resource == 'Item':
            context.execution = context.service.executions.create(
                service_id=context.service.id,
                resource=resource,
                sync=sync,
                item_id=context.item.id,
                dataset_id=context.dataset.id,
            )
        elif resource == 'Dataset':
            context.execution = context.service.executions.create(
                service_id=context.service.id,
                resource=resource,
                sync=sync,
                dataset_id=context.dataset.id,
            )
        elif resource == 'Annotation':
            context.execution = context.service.executions.create(
                service_id=context.service.id,
                resource=resource,
                sync=sync,
                item_id=context.item.id,
                dataset_id=context.dataset.id,
                annotation_id=context.annotation.id
            )
        elif resource == 'no_input':
            context.execution = context.service.executions.create(
                service_id=context.service.id,
                project_id=context.project.id,
                sync=sync
            )

    if sync:
        assert context.execution.latest_status['status'] == 'success'


@behave.then(u"I receive an Execution entity")
def step_impl(context):
    assert isinstance(context.execution, context.dl.entities.Execution)


@behave.then(u'Execution was executed on "{resource_type}"')
def step_impl(context, resource_type):
    num_try = 60
    interval = 5
    success = False

    for i in range(num_try):
        time.sleep(interval)
        execution = context.service.executions.get(execution_id=context.execution.id)
        if execution.latest_status['status'] == 'success':
            success = True
            break
        if execution.latest_status['status'] == 'failed':
            success = False
            break
    assert success, f"TEST FAILED: after {round(num_try * interval / 60, 1)} minutes"


@behave.then(u'Execution output is "{execution_output}"')
def step_impl(context, execution_output):
    execution = context.service.executions.get(execution_id=context.execution.id)
    assert execution.output == execution_output, f"Wrong execution result Expected: {execution_output} got: {execution.output}"


@behave.then(u'Execution was executed and finished with status "{execution_status}"')
@behave.then(u'Execution was executed and finished with status "{execution_status}" and message "{message}"')
def step_impl(context, execution_status, message=None):
    success = False
    num_try = 70
    interval = 10
    for i in range(num_try):
        execution = context.service.executions.get(execution_id=context.execution.id)
        if execution.latest_status['status'] == execution_status:
            success = True
            if message:  # message is not None
                assert execution.latest_status['message'] == message
            break
        elif execution.latest_status['status'] != execution_status and execution.latest_status['status'] not in [
            'in-progress', 'inProgress', 'created', 'pending']:
            break
        time.sleep(interval)

    assert success, f"TEST FAILED: Execution status is {execution.latest_status['status']}, after {round(num_try * interval / 60, 1)} minutes"


@behave.given(u'I upload item in "{item_path}" to dataset')
def step_impl(context, item_path):
    item_path = os.path.join(os.environ['DATALOOP_TEST_ASSETS'], item_path)
    context.item = context.dataset.items.upload(local_path=item_path)


@behave.then(u'Execution input is a valid itemId')
def step_impl(context):
    execution = context.execution
    assert execution.input['items'] == [context.item_id]


@behave.given(u'A service that receives items input')
def step_impl(context):
    def run(items):
        return items

    context.service = context.project.services.deploy(
        service_name='items-input-{}'.format(''.join(random.choice(string.ascii_lowercase) for i in range(5))),
        func=run,
        runtime=context.dl.KubernetesRuntime(
            autoscaler=context.dl.KubernetesRabbitmqAutoscaler(
                min_replicas=0,
                max_replicas=0
            )
        )
    )
    context.to_delete_services_ids.append(context.service.id)


@behave.when(u'I upload item in "{item_path}"')
def step_impl(context, item_path):
    item_path = os.path.join(os.environ['DATALOOP_TEST_ASSETS'], item_path)
    context.item = context.dataset.items.upload(local_path=item_path)


@behave.when(u'I execute pipeline with input type "{input_type}"')
def step_impl(context, input_type):
    if input_type == "None":
        execution_input = None
    elif input_type == context.dl.PackageInputType.ITEM:
        execution_input = list()
        execution_input.append(context.dl.FunctionIO(
            type=context.dl.PackageInputType.ITEM,
            value={'item_id': context.item.id},
            name='item'))
    elif input_type == context.dl.PackageInputType.MODEL:
        execution_input = list()
        execution_input.append(context.dl.FunctionIO(
            type=context.dl.PackageInputType.MODEL,
            value={'model_id': context.model.id},
            name='model'))
    else:
        raise ValueError("input_type must be 'None' or 'Item'")

    context.execution = context.pipeline.execute(
        execution_input=execution_input)


@behave.when(u'I add a service to the DPK')
def step_impl(context):
    context.dpk.components.services.append({
        'name': 'test-service-{}'.format(str(random.randrange(0, 1000))),
        'moduleName': context.dpk.components.modules[0].name
    })


@behave.when(u'I run predict on the item with the model from the app')
def step_impl(context):
    models = context.project.models.list().items
    context.model = [model for model in models if model.app['id'] == context.app.id][0]
    context.model_predict_execution = context.model.predict(item_ids=[context.item.id])


@behave.when(u'I execute the app service')
def step_impl(context):
    services = context.project.services.list().items
    context.service = [service for service in services if service.app['id'] == context.app.id][0]
    module = context.dpk.components.modules[0]
    func = [f for f in module.functions if f.name == 'predict_items'][0]
    context.service_executions = context.service.execute(
        execution_input={'items': [context.item.id]},
        project_id=context.project.id,
        function_name=func.name
    )


@behave.then(u'Both executions should have app and driverId')
def step_impl(context):
    interval = 5
    max_wait = 5 * 60
    success = False
    start = time.time()
    executions = [context.model_predict_execution, context.service_executions]
    errors = []
    assertions = []

    def validate(statement, error_message):
        if not statement:
            errors.append(error_message)
        assertions.append(statement)

    while not success and time.time() - start < max_wait:
        assertions = []
        errors = []
        for execution in executions:
            execution = context.service.executions.get(execution_id=execution.id)
            validate(execution.driver_id is not None and execution.driver_id == context.service.driver_id,
                     f"driver_id is not equal to service driver_id for execution {execution.id}")
            validate(execution.app is not None and execution.app['id'] == context.app.id,
                     f"app id is not equal to context app id for execution {execution.id}")
            validate(execution.latest_status['status'] in ['success', 'failed'],
                     f"execution status is not success for execution {execution.id}")

        success = all(assertions)
        if success:
            break
        time.sleep(interval)

    assert success, f"TEST FAILED: after {max_wait} seconds. Errors: {errors}"
