import time

import behave


@behave.when(u'I create a pipeline with name "{test_pipeline}"')
def step_impl(context, test_pipeline):
    payload = {'name': test_pipeline,
               'projectId': context.project.id,
               'nodes': [],
               'connections': []}

    context.pipeline = context.project.pipelines.create(pipeline_json=payload)
    context.to_delete_pipelines_ids.append(context.pipeline.id)


@behave.when(u'I get pipeline by the name of "{test_pipeline}"')
def step_impl(context, test_pipeline):
    context.pipeline_get = context.project.pipelines.get(pipeline_name=test_pipeline)


@behave.then(u'I get a pipeline entity')
def step_impl(context):
    assert 'Pipeline' in str(type(context.pipeline))


@behave.then(u'It is equal to pipeline created')
def step_impl(context):
    pipeline_json = context.pipeline.to_json()
    get_pipeline_json = context.pipeline_get.to_json()
    assert pipeline_json == get_pipeline_json


@behave.when(u'i list a project pipelines i get "{list_len}"')
def step_impl(context, list_len):
    assert context.project.pipelines.list().items_count == int(list_len)


@behave.when(u'I get pipeline execution in index "{index}"')
def step_impl(context, index):
    context.pipeline_execution = context.pipeline.pipeline_executions.list().items[int(index)]


@behave.then(u'Pipeline has "{total}" cycle executions')
def step_impl(context, total):
    num_try = 10
    interval = 6
    validate = 0
    success = False

    for i in range(num_try):
        time.sleep(interval)
        total_pipeline_executions = context.pipeline.pipeline_executions.list().items_count
        if total_pipeline_executions == int(total):
            validate += 1
            if validate == 2:
                success = True
                break

    assert success, "TEST FAILED: Expected to get {}, Actual got {}".format(total, total_pipeline_executions)
