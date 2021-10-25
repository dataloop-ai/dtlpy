import behave
import logging
import json


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
