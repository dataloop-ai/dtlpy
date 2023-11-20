import os
import json
from behave import given, when, then
import random


@given(
    'Pipeline which have a model variable and predict ml node that reference to this model variable file "{file_name}"')
def step_impl(context, file_name):
    pipeline_path = os.path.join(os.environ['DATALOOP_TEST_ASSETS'], "pipeline_flow", file_name)

    with open(pipeline_path, 'r') as f:
        pipeline_json = json.load(f)
    try:
        context.pipeline = context.project.pipelines.get(pipeline_name='ml-pipeline')
    except Exception as e:
        pipeline_json['projectId'] = context.project.id
        if not hasattr(context, "model"):
            context.model = context.project.models.list()[0][0]
        context.pipeline = context.project.pipelines.create(name=f'ml-pipeline-{random.randrange(100, 1000)}',
                                                            pipeline_json=pipeline_json, project_id=context.project.id)
        var = context.dl.Variable({'name': 'model_entity', 'value': context.model.id, 'type': 'Model'})
        context.pipeline.variables.append(var)
        context.pipeline.nodes[0].metadata['variableModel'] = 'model_entity'
        context.pipeline.nodes[0].project_id = context.project.id
        context.pipeline.nodes[0].namespace.project_name = context.project.name
        context.pipeline = context.pipeline.update()
        context.to_delete_pipelines_ids.append(context.pipeline.id)


@when('I update the model variable and the pipeline is still installed')
def step_impl(context):
    models = context.project.models.list()[0]
    for model in models:
        if model.id != context.model.id:
            context.model = model
            break
    context.pipeline.variables[0].value = context.model.id
    context.pipeline.pipelines.__update_variables(pipeline=context.pipeline)
    context.pipeline = context.project.pipelines.get(pipeline_id=context.pipeline.id)


@then('The pipeline installed successfully and model id placed correctly in the service initInputs')
def step_impl(context):
    if context.pipeline.status != 'Installed':
        assert False, 'pipeline status is not installed'
    service = context.project.services.list()[0][0]
    assert service.init_input['model_entity'] == context.pipeline.variables[0].value, 'model id is not correct'
