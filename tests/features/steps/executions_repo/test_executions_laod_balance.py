from multiprocessing.pool import ThreadPool
from behave import given, when, then
import datetime
import string
import random
import time


def run(st, progress):
    for j in range(50):
        progress.update(progress=j * 2)
    return st


def random_5_chars():
    return "".join(random.choices(string.ascii_lowercase + string.digits, k=5)) + "a"


@given(u'a service that run many executions')
def step_impl(context):
    context.busy_service = context.project.services.deploy(
        service_name=f'lb-test-{random_5_chars()}',
        func=run,
        active=False,
        runtime=context.dl.KubernetesRuntime(
            pod_type=context.dl.InstanceCatalog.REGULAR_XS,
            concurrency=10,
            autoscaler=context.dl.KubernetesRabbitmqAutoscaler(
                min_replicas=3,
                max_replicas=3
            )
        )
    )
    assert context.busy_service.active == False
    context.busy_service = context.project.services.get(
        service_id=context.busy_service.id
    )
    pool = ThreadPool(32)

    def execute():
        context.busy_service.execute(
            function_name="run",
            execution_input={"st": "Hello World"},
            project_id=context.project.id
        )

    for i in range(30000):
        pool.apply_async(execute)

    pool.close()
    pool.join()


@given(u'a scaled up regular service')
def step_impl(context):
    context.regular_service = context.project.services.deploy(
        service_name=f'lb-test-{random_5_chars()}',
        func=run,
        runtime=context.dl.KubernetesRuntime(
            pod_type=context.dl.InstanceCatalog.REGULAR_S,
            concurrency=100,
            autoscaler=context.dl.KubernetesRabbitmqAutoscaler(
                min_replicas=1,
                max_replicas=1
            )
        )
    )

    execution: context.dl.Execution = context.regular_service.execute(
        execution_input={"st": "Hello World"},
        function_name="run",
        project_id=context.project.id
    )
    start_time = time.time()
    timeout = 2 * 60
    while execution.latest_status['status'] != "success" and time.time() - start_time < timeout:
        time.sleep(1)
        execution = context.regular_service.executions.get(
            execution_id=execution.id
        )


@when(u'the regular service is executed while the noisy neighbor service is running')
def step_impl(context):
    context.busy_service.resume()
    filters = context.dl.Filters(resource=context.dl.FiltersResource.EXECUTION)
    filters.add(field="serviceId", values=context.busy_service.id)
    filters.add(field='latestStatus.status', values="success")
    executions = context.project.executions.list(filters=filters)
    while len(executions) == 0:
        time.sleep(1)
        executions = context.project.executions.list(filters=filters)

    context.single_execution = context.regular_service.execute(
        function_name="run",
        project_id=context.project.id,
        execution_input={"st": "Hello World"},
    )


@then(u'the noisy neighbor service should not affect the regular service execution time')
def step_impl(context):
    start_time = time.time()
    timeout = 5
    while context.single_execution.latest_status['status'] != "success" and time.time() - start_time < timeout:
        time.sleep(1)
        context.single_execution = context.regular_service.executions.get(
            execution_id=context.single_execution.id
        )

    assert context.single_execution.latest_status['status'] == "success", \
        "Regular service execution failed did not finish in time"
    execution_creation_time = datetime.datetime.strptime(context.single_execution.created_at, "%Y-%m-%dT%H:%M:%S.%fZ")
    execution_end_time = datetime.datetime.strptime(context.single_execution.updated_at, "%Y-%m-%dT%H:%M:%S.%fZ")
    execution_duration = execution_end_time - execution_creation_time
    total_seconds = execution_duration.total_seconds()
    assert total_seconds < 1, \
        "Regular service execution duration is too long. Actual duration: {}".format(total_seconds)
    context.regular_service.delete()
    context.busy_service.delete()
