from behave import when, then
import time
import dtlpy as dl
import json


@when(u'I wait for video services to finish')
def step_impl(context):
    context.item = context.dataset.items.get(item_id=context.item.id)
    num_try = 60
    interval = 10
    finished = False

    context.filters = context.dl.Filters(resource=dl.FiltersResource.EXECUTION)
    context.filters.add(field="resources.type", values="Item")
    context.filters.add(field="resources.id", values=context.item.id)

    for i in range(num_try):
        time.sleep(interval)
        executions_list = context.project.executions.list(filters=context.filters).items
        if {"success"} == set([exec.latest_status['status'] for exec in executions_list]):
            finished = True
            break

    return finished


@then(u'I validate execution status item metadata have the right message')
def step_impl(context):
    context.item = context.dataset.items.get(item_id=context.item.id)
    num_try = 6
    interval = 10
    has_error = False

    for i in range(num_try):
        time.sleep(interval)
        if 'errors' in context.item.metadata['system'].keys():
            error_message = [{"type": "origExpectedFrames",
                              "message": "Frames is not equal to FPS * (Duration - StartTime)", "value": 3,
                              "service": "VideoPreprocess"}]
            error = json.dumps(context.item.metadata['system']['errors'])
            err_message = "TEST FAILED: Wrong error message.\nExpected: {}\nGot: {}".format(
                error_message,
                context.item.metadata['system']['errors']
            )
            assert 'origExpectedFrames' in error, err_message
            assert 'Frames is not equal to FPS * (Duration - StartTime)' in error, err_message

            has_error = True
            break

    return has_error
