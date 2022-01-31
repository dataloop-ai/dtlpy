import behave
import time


@behave.then(u'Service was triggered on "{resource_type}" again')
def step_impl(context, resource_type):
    context.trigger_type = resource_type
    num_try = 60
    interval = 10
    triggered = False

    for i in range(num_try):
        time.sleep(interval)
        if resource_type == 'item':
            item = context.dataset.items.get(item_id=context.uploaded_item_with_trigger.id)
            if 'executionLogs' in item.system:
                if context.service.name in item.system['executionLogs']:
                    service_execution_log = item.system['executionLogs'][context.service.name]
                    if len(service_execution_log[context.service.module_name][context.trigger.function_name]) == 2:
                        triggered = True
                        break
        elif resource_type == 'annotation':
            item = context.annotation.item.annotations.get(annotation_id=context.annotation.id)
            if item.label == "Edited":
                triggered = True
                break
        elif resource_type == 'dataset':
            if context.service.executions.list().items_count == 2:
                execution = context.service.executions.list()[0][0]
                assert resource_type in execution.input.keys()
                execution = context.service.executions.list()[0][1]
                assert resource_type in execution.input.keys()
                triggered = True
                break

    assert triggered
