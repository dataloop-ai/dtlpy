import behave
import time


@behave.then(u'Service was triggered on "{resource_type}" again')
def step_impl(context, resource_type):
    context.trigger_type = resource_type
    num_try = 60
    interval = 15
    triggered = False

    for i in range(num_try):
        time.sleep(interval)
        if resource_type == 'item':
            filters = context.dl.Filters(resource=context.dl.FiltersResource.EXECUTION)
            filters.add(field='serviceId', values=context.service.id)
            filters.add(field='resources.id', values=context.uploaded_item_with_trigger.id)
            execution_page = context.service.executions.list(filters=filters)
            if execution_page.items_count == 2:
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
        elif resource_type == 'task':
            if context.service.executions.list().items_count == 2:
                execution = context.service.executions.list()[0][0]
                assert resource_type in execution.input.keys()
                execution = context.service.executions.list()[0][1]
                assert resource_type in execution.input.keys()
                triggered = True
                break
        elif resource_type == 'assignment':
            if context.service.executions.list().items_count == 2:
                execution = context.service.executions.list()[0][0]
                assert resource_type in execution.input.keys()
                execution = context.service.executions.list()[0][1]
                assert resource_type in execution.input.keys()
                triggered = True
                break

    assert triggered, f"TEST FAILED: After {round(num_try * interval / 60, 1)} minutes"
