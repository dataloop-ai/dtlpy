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

        context.execution = context.service.executions.create(
            service_id=context.service.id,
            sync=sync,
            execution_input=execution_inputs,
            timeout=300)
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
    assert success


@behave.then(u'Execution was executed and finished with status "{execution_status}"')
def step_impl(context, execution_status):
    success = False
    num_try = 60
    interval = 15
    for i in range(num_try):
        execution = context.service.executions.get(execution_id=context.execution.id)
        if execution.latest_status['status'] == execution_status:
            success = True
            break
        time.sleep(interval)

    assert success, "TEST FAILED: Execution status is {}".format(execution.latest_status['status'])


@behave.given(u'I upload item in "{item_path}" to dataset')
def step_impl(context, item_path):
    item_path = os.path.join(os.environ['DATALOOP_TEST_ASSETS'], item_path)
    context.item = context.dataset.items.upload(local_path=item_path)


@behave.when(u'I upload item in "{item_path}"')
def step_impl(context, item_path):
    item_path = os.path.join(os.environ['DATALOOP_TEST_ASSETS'], item_path)
    context.item = context.dataset.items.upload(local_path=item_path)


@behave.when(u'I execute pipeline with input type "{input_type}"')
def step_impl(context, input_type):
    execution_input = list()
    if input_type == 'Item':
        execution_input.append(context.dl.FunctionIO(
            type='Item',
            value={'item_id': context.item.id},
            name='item'))

    context.execution = context.pipeline.execute(
        execution_input=execution_input)
