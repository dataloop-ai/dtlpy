import behave
from operator import attrgetter
import time


@behave.then(u'I validate pipeline execution params include node executions "{node_exec_flag}"')
def step_impl(context, node_exec_flag):
    executions_val = list()
    for row in context.table:
        test_value = row['value']
        #  Add the pipeline cycle_execution creator
        executions_val.append(attrgetter(row['key'])(context.execution))

        if eval(node_exec_flag):
            time.sleep(7)
            context.execution = context.pipeline.pipeline_executions.get(context.execution.id)
            for i in range(0, 10):
                if context.execution.status == "pending":
                    time.sleep(7)
                    context.execution = context.pipeline.pipeline_executions.get(context.execution.id)
                else:
                    break
            assert context.execution.executions, "TEST FAILED: Executions empty.{}".format(context.execution.executions)
            for execution in context.execution.executions.values():
                assert isinstance(execution, list), "TEST FAILED: execution Should be a list"
                #  Add the pipeline cycle connected executions creator
                execution_id = execution[0]['_id']
                executions = context.dl.executions.get(execution_id=execution_id)
                executions_val.append(attrgetter(row['key'])(executions))

        if row['value'] == "current_user":
            test_value = context.dl.info()['user_email']
        elif row['value'] == "piper":
            test_value = ["piper@dataloop.ai", "pipelines@dataloop.ai"]
        for val in executions_val:
            assert isinstance(val, str), "TEST FAILED: val must be a string"
            assert val in test_value, "TEST FAILED: Expected to get {}, Actual got {}".format(test_value, val)


@behave.then(u'I validate pipeline execution params')
def step_impl(context, node_exec_flag):
    executions_val = list()
    for row in context.table:
        test_value = row['value']
        executions_val.append(attrgetter(row['key'])(context.execution))

        if eval(node_exec_flag):
            time.sleep(5)
            context.execution = context.pipeline.pipeline_executions.get(context.execution.id)
            assert context.execution.executions, "TEST FAILED: Executions empty.{}".format(context.execution.executions)
            for execution in context.execution.executions.values():
                assert isinstance(execution, list), "TEST FAILED: execution Should be a list"
                execution_id = execution[0]['_id']
                executions = context.dl.executions.get(execution_id=execution_id)
                executions_val.append(attrgetter(row['key'])(executions))

        if row['value'] == "current_user":
            test_value = context.dl.info()['user_email']
        for val in executions_val:
            assert val == test_value, "TEST FAILED: Expected to get {}, Actual got {}".format(test_value, val)


@behave.then(u'I wait for item to enter task')
def step_impl(context):
    timeout = 60 * 5 * 1000
    start_time = time.time()
    success = False
    while time.time() < start_time + timeout:
        context.item = context.dataset.items.get(item_id=context.item.id)
        if len(context.item.system['refs']) > 1:
            success = True
            break
    assert success, "TEST FAILED: Item did not enter task"


@behave.then(u'I expect that pipeline execution has "{execution_number}" success executions')
def step_impl(context, execution_number):
    time.sleep(2)
    assert context.pipeline.pipeline_executions.list().items_count != 0, "Pipeline not executed found 0 executions"
    context.pipeline = context.project.pipelines.get(context.pipeline.name)

    num_try = 80
    interval = 10
    executed = False
    execution_count = 0
    pipeline_executions = None
    for i in range(num_try):
        time.sleep(interval)
        context.cycles = context.pipeline.pipeline_executions.list().items
        cycle = context.cycles[0]
        execution_list = cycle.executions
        execution_count = 0
        for ex in execution_list.values():
            execution_count = execution_count + len(ex)
        if execution_count == int(execution_number):
            # validate no other executions were created
            filters = context.dl.Filters(resource=context.dl.FiltersResource.EXECUTION)
            filters.add(field='pipeline.executionId', values=cycle.id)
            filters.add(field='pipeline.id', values=context.pipeline.id)
            pipeline_executions = context.dl.executions.list(filters=filters)
            execution_count = pipeline_executions.items_count
            executed = execution_count == int(execution_number)
            break

    if pipeline_executions and pipeline_executions.items[-1].latest_status['status'] == 'failed':
        assert False, f"TEST FAILED: Last execution failed with message: {pipeline_executions.items[-1].latest_status['message']}"
    assert executed, "TEST FAILED: Pipeline has {} executions instead of {}".format(execution_count, execution_number)
    return executed


@behave.when(u'I get pipeline cycle execution in index "{num}"')
def step_impl(context, num):
    filters = context.dl.Filters()
    filters.resource = context.dl.FiltersResource.PIPELINE_EXECUTION
    context.execution = context.pipeline.pipeline_executions.list(filters=filters).items[eval(num)]


@behave.then(u'I validate Cycle execution status is "{status}"')
def step_impl(context, status):
    num_try = 60
    interval = 10
    executed = False
    context.pipeline_execution_id = context.pipeline_execution.id

    for i in range(num_try):
        time.sleep(interval)
        context.pipeline_execution = context.pipeline.pipeline_executions.get(pipeline_execution_id=context.pipeline_execution_id)
        if context.pipeline_execution.status == status:
            executed = True
            break

    assert executed, "TEST FAILED: Pipeline cycle status is {} Expected to get {}".format(context.pipeline_execution.status, status)
    return executed
