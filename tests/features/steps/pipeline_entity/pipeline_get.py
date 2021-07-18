import behave


@behave.when(u'I create a pipeline with name "{test_pipeline}"')
def step_impl(context, test_pipeline):
    payload = {'name': test_pipeline,
               'projectId': context.project.id,
               'nodes': [],
               'connections': []}

    context.pipeline = context.project.pipelines.create(payload)
    context.to_delete_pipelines_ids.append(context.pipeline.id)


@behave.when(u'I get pipeline by the name of "{test_pipeline}"')
def step_impl(context, test_pipeline):
    context.pipeline_get = context.project.pipelines.get(pipeline_name=test_pipeline)


@behave.then(u'I get a pipeline entity')
def step_impl(context):
    assert 'Pipeline' in str(type(context.pipeline))


@behave.then(u'It is equal to pipeline created')
def step_impl(context):
    assert context.pipeline.to_json() == context.pipeline_get.to_json()


@behave.when(u'i list a project pipelines i get "{list_len}"')
def step_impl(context, list_len):
    assert context.project.pipelines.list().items_count == int(list_len)
