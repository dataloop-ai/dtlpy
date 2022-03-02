import behave
import time


@behave.when(u"I create an execution for all functions")
def step_impl(context):
    context.first_module_first_function_execution = context.first_service.executions.create(
        service_id=context.first_service.id,
        sync=True,
        stream_logs=False,
        return_output=False,
        execution_input=context.dl.FunctionIO(
            type='Item',
            value={'item_id': context.item.id},
            name='item'),
        function_name='first',
        timeout=300)
    context.first_module_second_function_execution = context.first_service.executions.create(
        service_id=context.first_service.id,
        sync=True,
        stream_logs=False,
        return_output=False,
        execution_input=context.dl.FunctionIO(
            type='Item',
            value={'item_id': context.item.id},
            name='item'),
        function_name='second',
        timeout=300)
    context.second_module_first_function_execution = context.second_service.executions.create(
        service_id=context.second_service.id,
        sync=True,
        stream_logs=False,
        return_output=False,
        execution_input=context.dl.FunctionIO(
            type='Item',
            value={'item_id': context.item.id},
            name='item'),
        function_name='first',
        timeout=300)
    context.second_module_second_function_execution = context.second_service.executions.create(
        service_id=context.second_service.id,
        sync=True,
        stream_logs=False,
        return_output=False,
        execution_input=context.dl.FunctionIO(
            type='Item',
            value={'item_id': context.item.id},
            name='item'),
        function_name='second',
        timeout=300)


@behave.then(u'Execution was executed on item for all functions')
def step_impl(context):
    # get new item
    item = context.dl.items.get(item_id=context.item.id)
    try:
        success = item.metadata['user']['first_module_first_function'] and \
                  item.metadata['user']['first_module_second_function'] and \
                  item.metadata['user']['second_module_first_function'] and \
                  item.metadata['user']['second_module_second_function']
    except:
        success = False
    assert success
