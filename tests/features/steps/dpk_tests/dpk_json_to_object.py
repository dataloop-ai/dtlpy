import json
import os

import behave


@behave.when(u"I fetch the dpk from '{file_name}' file")
@behave.given(u"I fetch the dpk from '{file_name}' file")
def step_impl(context, file_name):
    path = os.path.join(os.environ['DATALOOP_TEST_ASSETS'], file_name)
    with open(path, 'r') as file:
        json_object = json.load(file)
    context.dpk = context.dl.entities.Dpk.from_json(_json=json_object,
                                                    client_api=context.dl.client_api,
                                                    project=context.dl.entities.Project.from_json({},
                                                                                                  context.dl.client_api,
                                                                                                  False)
                                                    )
    context.json_object = json_object


@behave.then(u"I have a dpk entity")
def step_impl(context):
    assert hasattr(context, 'dpk')


@behave.then(u"I have json object to compare")
def step_impl(context):
    assert hasattr(context, 'json_object')


@behave.then(u"The dpk is filled with the same values")
def step_impl(context):
    if 'name' in context.json_object:
        assert context.dpk.name == context.json_object['name']
    if 'id' in context.json_object:
        assert context.dpk.id == context.json_object['id']
    if 'scope' in context.json_object:
        assert context.dpk.scope == context.json_object['scope']
    if 'version' in context.json_object:
        assert context.dpk.version == context.json_object['version']
    if 'creator' in context.json_object:
        assert context.dpk.creator == context.json_object['creator']
    if 'displayName' in context.json_object:
        assert context.dpk.display_name == context.json_object['displayName']
    if 'description' in context.json_object:
        assert context.dpk.description == context.json_object['description']
    if 'icon' in context.json_object:
        assert context.dpk.icon == context.json_object['icon']
    if 'categories' in context.json_object:
        assert context.dpk.categories == context.json_object['categories']
    if 'components' in context.json_object:
        assert context.dl.entities.Dpk.components_to_json(context.dpk.components)['panels'] == \
               context.json_object['components']['panels']
    if 'createdAt' in context.json_object:
        assert context.dpk.created_at == context.json_object['createdAt']
    if 'updatedAt' in context.json_object:
        assert context.dpk.updated_at == context.json_object['updatedAt']
    if 'codebase' in context.json_object:
        assert context.dpk.codebase == context.json_object['codebase']
    if 'url' in context.json_object:
        assert context.dpk.url == context.json_object['url']
    if 'tags' in context.json_object:
        assert context.dpk.tags == context.json_object['tags']


@behave.given(u"I publish a dpk to the platform")
def step_impl(context):
    context.dpk = context.dl.entities.Dpk.publish(context.dpk)
