import json
import os
import random

import behave
from .. import fixtures
from ..pipeline_entity import test_pipeline_interface
import random
from operator import attrgetter


@behave.when(u"I fetch the dpk from '{file_name}' file")
@behave.given(u"I fetch the dpk from '{file_name}' file")
def step_impl(context, file_name):
    path = os.path.join(os.environ['DATALOOP_TEST_ASSETS'], file_name)
    with open(path, 'r') as file:
        json_object = json.load(file)

    json_object = fixtures.update_dtlpy_version(json_object)
    if "context" in json_object.keys():
        if json_object['context'].get("project", None) is not None:
            json_object['context']['project'] = context.project.id
        if json_object['context'].get("organization", None) is not None:
            json_object['context']['organization'] = context.project.org['id']

    if "pipelineTemplates" in json_object.get('components', {}).keys():
        json_object['components']['pipelineTemplates'][0] = test_pipeline_interface.generate_pipeline_json(context,
                                                                                                           json_object[
                                                                                                               'components'][
                                                                                                               'pipelineTemplates'][
                                                                                                               0])

    context.dpk = context.dl.entities.Dpk.from_json(_json=json_object,
                                                    client_api=context.dl.client_api,
                                                    project=context.project
                                                    )
    context.json_object = json_object


@behave.when(u"I add codebase to dpk")
@behave.given(u"I add codebase to dpk")
def step_impl(context):
    context.dpk.codebase = context.codebase


@behave.when(u"I add integration to dpk")
def step_impl(context):
    if context.dpk.components.services:
        for service in context.dpk.components.services:
            if 'integrations' in service:
                service['integrations'][0]['value'] = context.integration.id
    if context.dpk.components.compute_configs:
        for service in context.dpk.components.compute_configs:
            if service.integrations:
                service.integrations[0]['value'] = context.integration.id
    if context.dpk.components.integrations:
        for integration in context.dpk.components.integrations:
            if 'value' in integration:
                integration['value'] = context.integration.id


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
    if 'attributes' in context.json_object:
        assert context.dpk.attributes == context.json_object['attributes']
    if 'components' in context.json_object:
        assert context.dpk.components.panels == \
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
    context.dpk.name = context.dpk.name + str(random.randint(10000, 1000000))
    context.dpk = context.project.dpks.publish(context.dpk)
    if hasattr(context.feature, 'dpks'):
        context.feature.dpks.append(context.dpk)
    else:
        context.feature.dpks = [context.dpk]


@behave.when(u"I update dpk dtlpy to current version for service in index {i}")
def step_impl(context, i):
    context.dpk.components.services[int(i)]['versions'] = {'dtlpy': context.dl.__version__, "verify": True}


@behave.when(u"I remove the last service from context.custom_installation")
def step_impl(context):
    if not hasattr(context, "custom_installation"):
        raise AttributeError(
            "Please make sure to add 'custom_installation' to 'context', Can use step 'When I create a context.custom_installation var'")

    context.custom_installation.get('components').get('services').pop(-1)
    context.custom_installation.get('components').get('triggers').pop(-1)


@behave.when(u"I add service to context.custom_installation")
def step_impl(context):
    if not hasattr(context, "custom_installation"):
        raise AttributeError(
            "Please make sure to add 'custom_installation' to 'context', Can use step 'When I create a context.custom_installation var'")

    service = context.custom_installation.get('components').get('services')[-1].copy()
    service['name'] = f"{service.get('name')}-sdk"
    context.custom_installation.get('components').get('services').append(service)


@behave.when(u"I add att '{value}' to dpk '{component}' in index '{index}'")
def step_impl(context, value, component, index):
    if "=" in value:
        value = value.split("=")
        if '.id' in value[1]:
            value[1] = attrgetter(value[1])(context)
        elif '[' in value[1] or '{' in value[1]:
            value[1] = eval(value[1])
    else:
        raise ValueError("Please make sure 'value' structure is 'key=val'")

    if component == 'service':
        if "cooldownPeriod" in value:
            context.dpk.components.services[int(index)]['runtime']['autoscaler'][value[0]] = eval(value[1])
    elif component == 'model':
        model = context.dpk.components.models[int(index)]
        if "metadata" in value[0]:
            if "system" in value[0]:
                model['metadata']['system'][value[0].split('.')[-1]] = value[1]
            else:
                model['metadata'][value[0].split('.')[-1]] = value[1]
        else:
            model[value[0]] = value[1]
    else:
        raise ValueError("Please provide a valid dpk component")


@behave.then(u"I validate dpk autoscaler in composition for service in index '{index}'")
def step_impl(context, index):
    context.dpk = context.project.dpks.get(dpk_id=context.dpk.id)
    app_composition = context.project.compositions.get(context.app.composition_id)

    dpk_autoscaler_items = context.dpk.components.services[int(index)]['runtime']['autoscaler'].items()
    comp_autoscaler_items = app_composition['spec'][int(index)]['runtime']['autoscaler'].items()

    assert dpk_autoscaler_items <= comp_autoscaler_items, f"TEST FAILED: dpk_autoscaler_items is {dpk_autoscaler_items} composition_autoscaler_items is {comp_autoscaler_items}"


@behave.given(u'I remove the "{entity}" from integration from the dpk in "{component}" component in index {index}')
def step_impl(context, entity, component, index):
    if component == 'integrations':
        eval(f"context.dpk.components.{component}[{index}].pop('{entity}')")
    else:
        eval(f"context.dpk.components.{component}[{index}]['integrations'][{index}].pop('{entity}')")


@behave.given(u'I add "{entity}" to integration from the dpk in "{component}" component in index {index}')
def step_impl(context, entity, component, index):
    if "=" in entity:
        entity = entity.split("=")
        if '.id' in entity[1]:
            entity[1] = attrgetter(entity[1])(context)
        elif '[' in entity[1] or '{' in entity[1]:
            entity[1] = eval(entity[1])
        elif entity[1] == "True" or entity[1] == "False":
            entity[1] = eval(entity[1])
        if component == 'integrations':
            eval(f"context.dpk.components.{component}[{index}].update({{entity[0]: entity[1]}})")
        else:
            eval(f"context.dpk.components.{component}[{index}]['integrations'][{index}].update({{entity[0]: entity[1]}})")
    else:
        raise ValueError("Please make sure 'entity' structure is 'key=val'")
