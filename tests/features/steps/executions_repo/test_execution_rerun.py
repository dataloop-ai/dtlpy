import behave
import time
import os
import random
import json


@behave.then(u'I validate execution response params')
def step_impl(context):
    execution_json = context.dl.executions.get(execution_id=context.execution.id).to_json()
    for row in context.table:
        assert execution_json[row['key']] == row[
            'value'], f"TEST FAILED: Expected {row['value']}, Actual {execution_json[row['key']]}"


@behave.when(u'I rerun the execution')
def step_impl(context):
    context.execution = context.execution.rerun(False)


@behave.when(u'I rerun the execution with batch function')
def step_impl(context):
    filters = context.dl.Filters(field='id', values=[context.execution.id],
                                 operator=context.dl.FiltersOperations.IN,
                                 resource=context.dl.FiltersResource.EXECUTION)

    command = context.dl.executions.rerun_batch(filters=filters)
    assert command is not None, "Failed to rerun batch execution"
    assert command.status == 'success', "Failed to rerun batch execution"
    context.execution = context.dl.executions.get(execution_id=context.execution.id)
