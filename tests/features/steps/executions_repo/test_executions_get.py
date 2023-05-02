import behave
import logging
import json
from operator import attrgetter


@behave.when(u"I get execution by id")
def step_impl(context):
    context.execution_get = context.service.executions.get(execution_id=context.execution.id)


@behave.then(u"I receive an Execution object")
def step_impl(context):
    assert isinstance(context.execution_get, context.dl.entities.Execution)


@behave.then(u"Execution received equals to execution created")
def step_impl(context):
    execution_get_json = context.execution_get.to_json()
    execution_json = context.execution.to_json()
    execution_get_json.pop('status')
    execution_json.pop('status')
    execution_get_json.pop('latestStatus')
    execution_json.pop('latestStatus')
    execution_get_json.pop('statusLog')
    execution_json.pop('statusLog')
    execution_get_json.pop('updatedAt')
    execution_json.pop('updatedAt')

    if execution_get_json != execution_json:
        logging.error(
            'FAILED: response json is:\n{}\n\nto_json is:\n{}'.format(json.dumps(context.execution_get.to_json(),
                                                                                 indent=2),
                                                                      json.dumps(context.execution.to_json(),
                                                                                 indent=2)))
        assert False


@behave.when(u'I get service execution by "{resource}"')
def step_impl(context, resource):
    resource_att = resource.split(".")
    filters = context.dl.Filters()
    filters.add(field="resource.type", values=resource_att[0])
    filters.add(field="resource.{}".format(resource_att[1]), values="{}".format(attrgetter(resource)(context)))
    filters.resource = context.dl.FiltersResource.EXECUTION
    context.execution = context.service.executions.list(filters=filters).items[0]


@behave.then(u"I validate execution params")
def step_impl(context):
    for row in context.table:
        value = row['value']
        execution_val = attrgetter(row['key'])(context.execution)

        if row['value'] == "current_user":
            value = context.dl.info()['user_email']
        elif row['value'] == "piper":
            value = ["piper@dataloop.ai", "pipelines@dataloop.ai"]
        assert execution_val in value, "TEST FAILED: Expected to get {}, Actual got {}".format(value, execution_val)


@behave.then(u"I validate params in executions list")
def step_impl(context):
    for execution in context.execution_list.items:
        for row in context.table:
            if "item.id" in row['value']:
                row['value'].replace('item.id', context.item.id)
            assert attrgetter(row['key'])(execution) == eval(row['value']), \
                "TEST FAILED: Expected to get {}, Actual got {}".format(eval(row['value']),
                                                                        attrgetter(row['key'])(context.execution))
