import behave
import time
import os
import random
import json


@behave.then(u'I validate execution response params')
def step_impl(context):
    execution_json = context.dl.executions.get(execution_id=context.execution.id).to_json()
    for row in context.table:
        assert execution_json[row['key']] == row['value'], f"TEST FAILED: Expected {row['value']}, Actual {execution_json[row['key']]}"


@behave.when(u'I rerun the execution')
def step_impl(context):
    context.execution = context.execution.rerun(False)
