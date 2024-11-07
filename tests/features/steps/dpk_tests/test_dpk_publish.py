import json
import os
import random
import behave


@behave.when(u'I publish a dpk to the platform')
@behave.when(u'I publish a dpk to the platform without random name "{random_name}"')
def step_impl(context, random_name=True):
    random_name = True if random_name != 'False' else False
    if random_name:
        context.dpk.name = context.dpk.name + str(random.randint(10000, 1000000))
    context.published_dpk = context.project.dpks.publish(context.dpk)
    if hasattr(context.feature, 'dpks'):
        context.feature.dpks.append(context.published_dpk)
    else:
        context.feature.dpks = [context.published_dpk]


@behave.when(u'dpk has base id')
def step_impl(context):
    assert context.dpk.base_id is not None


@behave.when(u'i save dpk base id')
def step_impl(context):
    context.dpk_base_id = context.dpk.base_id


@behave.then(u'i check the new dpk hase the same base id')
def step_impl(context):
    assert context.dpk_base_id == context.dpk.base_id, "Base id is not the same"
    assert context.dpk_base_id != context.dpk.id, "Base id is the same as id"


@behave.when(u'I try to publish a dpk to the platform')
def step_impl(context):
    try:
        context.dpk.name = context.dpk.name + str(random.randint(10000, 1000000))
        context.published_dpk = context.project.dpks.publish(context.dpk)
        if hasattr(context.feature, 'dpks'):
            context.feature.dpks.append(context.published_dpk)
        else:
            context.feature.dpks = [context.published_dpk]
        context.error = None
    except Exception as e:
        context.error = e


@behave.when(u'I publish without context')
def step_impl(context):
    try:
        context.dpk.name = context.dpk.name + str(random.randint(10000, 1000000))
        context.published_dpk = context.dl.dpks.publish(context.dpk)
        if hasattr(context.feature, 'dpks'):
            context.feature.dpks.append(context.published_dpk)
        else:
            context.feature.dpks = [context.published_dpk]
    except Exception as e:
        context.error = e


@behave.when(u'I add context to the dpk')
def step_impl(context):
    dpk_context = {
        "project": context.project.id
    }
    context.dpk.context = dpk_context
    context.dpk.scope = "organization"


@behave.when(u'I add pipeline template "{template_path}" to the dpk')
def step_impl(context, template_path):
    pipeline_template_path = template_path
    path = os.path.join(os.environ['DATALOOP_TEST_ASSETS'], pipeline_template_path)
    with open(path, 'r') as file:
        json_object = json.load(file)
    context.dpk.components[json_object["name"]] = {
        "type": "pipelineTemplate",
        "spec": json_object
    }


@behave.then(u'The pipeline template "{template}" should be created')
def step_impl(context, template):
    pipeline_template_name = context.dpk.components[template]["spec"]["name"]
    success, response = context.project._client_api.gen_request(req_type='POST', path='/pipelines/templates/query',
                                                                json_req={
                                                                    "org": {
                                                                        "filter": {
                                                                            "$and": [{"name": pipeline_template_name}]}
                                                                    }
                                                                })
    template = response.json()["org"]["items"][0]
    assert template["name"] == pipeline_template_name


@behave.when(u"I add the context.dataset to the dpk model")
def step_impl(context):
    for model in context.dpk.components.models:
        model['datasetId'] = context.dataset.id


@behave.then(u'The user defined properties should have the same values')
def step_impl(context):
    dpk = context.dpk
    p_dpk = context.published_dpk
    assert dpk.display_name == p_dpk.display_name
    assert dpk.version if dpk.version else "1.0.0" == p_dpk.version
    assert dpk.attributes == p_dpk.attributes
    assert dpk.icon == p_dpk.icon
    assert dpk.tags == p_dpk.tags
    assert dpk.scope == p_dpk.scope
    assert dpk.description == p_dpk.description
    assert dpk.components.to_json() == p_dpk.components.to_json()


@behave.then(u'id, name, createdAt, codebase, url and creator should have values')
def step_impl(context):
    dpk = context.published_dpk
    assert dpk.id is not None
    assert dpk.name is not None
    assert dpk.created_at is not None
    assert dpk.codebase is not None
    assert dpk.url is not None


@behave.when(u'I set the model in the context')
def step_impl(context):
    composition = context.project.compositions.get(composition_id=context.app.composition_id)
    context.model = context.project.models.get(model_id=composition["models"][0]["modelId"])


@behave.when(u'I add models list to context.models and expect to get "{total_models}" models')
@behave.then(u'I expect to get "{total_models}" models in project')
def step_impl(context, total_models):
    filters = context.dl.Filters()
    filters.resource = context.dl.FiltersResource.MODEL
    filters.sort_by(field='name', value=context.dl.FiltersOrderByDirection.ASCENDING)
    context.models = context.project.models.list(filters=filters).items
    assert len(context.models) == int(total_models), f"Expected {total_models} models, got {len(context.models)}"


@behave.when(u'I increment dpk version')
def step_impl(context):
    version = context.dpk.version.split('.')
    version[2] = str(int(version[2]) + 1)
    context.dpk.version = '.'.join(version)


@behave.when(u'I publish a dpk')
def step_impl(context):
    context.dpk = context.project.dpks.publish(context.dpk)
    if hasattr(context.feature, 'dpks'):
        context.feature.dpks.append(context.dpk)
    else:
        context.feature.dpks = [context.dpk]
