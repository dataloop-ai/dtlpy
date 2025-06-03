import behave
import json
import dictdiffer


@behave.when(u'I try get the "{dpk_obj}" by id')
def step_impl(context, dpk_obj):
    try:
        context.dpk = context.dl.dpks.get(dpk_id=getattr(context, dpk_obj).id)
        context.error = None
    except Exception as e:
        context.error = e


@behave.when(u'I get the dpk by name')
def step_impl(context):
    context.dpk = context.dl.dpks.get(dpk_name=context.published_dpk.name)


@behave.when(u'i update dpk compute config "{comp_name}" runtime "{filed}" to "{val}"')
def step_impl(context, comp_name, filed, val):
    for comp in context.dpk.components.compute_configs:
        if comp.name == comp_name:
            comp.runtime[filed] = val


@behave.when(u'i update dpk attribute "{filed}" to "{val}"')
def step_impl(context, filed, val):
    context.dpk.attributes[filed] = val


@behave.then(u'I have the same dpk as the published dpk')
def step_impl(context):
    to_json = context.dpk.to_json()
    if to_json.get('dependencies', False) is None:
        to_json.pop('dependencies', None)
    if 'context' in to_json and to_json['context'] is None:
        to_json.pop('context', None)
    assert to_json == context.published_dpk.to_json(), "TEST FAILED: Different in to_json and dpk.to_json().\n{}".format(
        list(dictdiffer.diff(to_json, context.published_dpk.to_json())))


@behave.when(u'I get a dpk with invalid id')
def step_impl(context):
    try:
        context.dpk = context.dl.dpks.get(dpk_id="1")
        context.error = None
    except Exception as e:
        context.error = e


@behave.then(u'I should get an exception')
def step_impl(context):
    assert context.error is not None


@behave.when(u'I get global dpk by name "{dpk_name}"')
def step_impl(context, dpk_name):
    try:
        context.dpk = context.dl.dpks.get(dpk_name=eval(dpk_name) if "context." in dpk_name else dpk_name)
        context.error = None
    except Exception as e:
        raise e


@behave.when(u'I try get the "{dpk_obj}" by name')
def step_impl(context, dpk_obj):
    try:
        context.dpk = context.project.dpks.get(dpk_name=getattr(context, dpk_obj).name)
        context.error = None
    except Exception as e:
        context.error = e


@behave.then(u'I validate attributes response in context.req')
def step_impl(context):
    if not hasattr(context, "req") or not hasattr(context, "response"):
        return False, "Context missing 'req' / 'response' attribute"

    parsed_response = json.loads(context.response.text)

    if isinstance(parsed_response, list):
        response_list = [list(att.values())[0] for att in parsed_response ]
        assert all(var in response_list for var in context.req.get("response", None)), \
            f"TEST FAILED: Expected {context.req.get('response', None)}, Received {response_list}"

    elif isinstance(parsed_response, dict):
        response_list = list(parsed_response.keys())
        assert all(var in response_list for var in context.req.get("response", [])), \
            f"TEST FAILED: Expected {context.req.get('response', None)}, Received {response_list}"

    else:
        raise TypeError("Unexpected JSON format: not a list or dictionary")


@behave.when(u'Get dpk app command from metadata')
def step_impl(context):
    context.dpk = context.project.dpks.get(dpk_id=context.dpk.id)
    command_id = context.dpk.metadata.get('commands', {}).get('apps', None)
    context.command = context.dl.commands.get(command_id=command_id, url='api/v1/commands/faas/{}'.format(command_id))
