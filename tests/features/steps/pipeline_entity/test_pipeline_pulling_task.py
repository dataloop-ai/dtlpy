import time
import dtlpy as dl
import behave


@behave.when(u'I create pipeline with pulling task with type "{task_type}" node and dataset node')
def step_impl(context, task_type):
    params = dict()
    for row in context.table:
        params[row['key']] = row['value']

    if params['priority'] == "LOW":
        params['priority'] = dl.TaskPriority.LOW
    elif params['priority'] == "MEDIUM":
        params['priority'] = dl.TaskPriority.MEDIUM
    elif params['priority'] == "HIGH":
        params['priority'] = dl.TaskPriority.HIGH
    else:
        "TEST FAILED: Please provide valid priority value : LOW / MEDIUM / HIGH"

    t = time.localtime()
    current_time = time.strftime("%H-%M-%S", t)
    context.pipeline_name = 'pipeline-{}'.format(current_time)

    context.pipeline = context.project.pipelines.create(name=context.pipeline_name)

    context.task_name = 'My Task-completed' + current_time
    context.task_node = dl.TaskNode(
        name=context.task_name,
        project_id=context.project.id,
        dataset_id=context.dataset.id,
        recipe_id=context.recipe.id,
        recipe_title=context.recipe.title,
        task_owner=context.dl.info()['user_email'],
        workload=[dl.WorkloadUnit(assignee_id=context.dl.info()['user_email'], load=100)],
        position=(1, 1),
        task_type=task_type,
        batch_size=int(params['batch_size']),
        max_batch_workload=int(params['max_batch_workload']),
        priority=params['priority']
    )

    dataset_node = dl.DatasetNode(
        name=context.dataset.name,
        project_id=context.project.id,
        dataset_id=context.dataset.id,
        position=(2, 2)
    )

    filters = context.dl.Filters()
    filters.add(field='datasetId', values=context.dataset.id)
    context.pipeline.nodes.add(context.task_node).connect(node=dataset_node, source_port=context.task_node.outputs[0])
    context.task_node.add_trigger(filters=filters)

    context.pipeline.update()
    pipeline = context.project.pipelines.get(pipeline_name=context.pipeline_name)
    pipeline.install()

    time.sleep(5)


@behave.when(u'I get task by pipeline task node')
def step_impl(context):
    try:
        pipeline_task_name = "{} ({})".format(context.task_name, context.pipeline_name)
        context.task = context.project.tasks.get(task_name=pipeline_task_name)
    except Exception as e:
        assert False, "Failed to get task with the name: {}\n{}".format(pipeline_task_name, e)


@behave.then(u'I validate pulling task created equal to pipeline task node')
def step_impl(context):
    assert context.task_node.task_type == context.task.spec['type'], "TEST FAILED: task_type Expected - {}, Got - {}".format(context.task_node.task_type, context.task.spec['type'])

    assert context.task_node.batch_size == context.task.metadata['system']['batchSize'], "TEST FAILED: batch_size Expected - {}, Got - {}".format(context.task_node.batch_size,
                                                                                                                                                  context.task.metadata['system']['batchSize'])

    assert context.task_node.max_batch_workload == context.task.metadata['system']['maxBatchWorkload'], "TEST FAILED: max_batch_workload Expected - {}, Got - {}".format(
        context.task_node.max_batch_workload, context.task.metadata['system']['maxBatchWorkload'])

    assert context.task_node.priority == context.task.priority, "TEST FAILED: priority Expected - {}, Got - {}".format(context.task_node.priority, context.task.priority)


@behave.then(u'I expect pipeline error to be "{pipeline_error}"')
def step_impl(context, pipeline_error):

    filters = context.dl.Filters(resource=context.dl.FiltersResource.COMPOSITION)
    filters.add(field='id', values=[context.pipeline.composition_id], operator=context.dl.FILTERS_OPERATIONS_IN)
    composition_response = context.dl.pipelines._list(filters=filters)
    assert composition_response['totalItemsCount'] == 1, "TEST FAILED: Composition expected : {} , Got : {}".format(1, composition_response['totalItemsCount'])
    assert pipeline_error in composition_response['items'][0]['errorText']['message'], "TEST FAILED: Wrong error message.\n{}".format(composition_response['items'][0]['errorText']['message'])


    # ToDo : After DAT-31746 fixed - need to update test to use this assertion
    # assert context.install_response['status'] == 'Failure', "TEST FAILED: Status expected: Failure, Got: {}".format(context.install_response['status'])
    # assert pipeline_error in context.install_response['errorText']['message'], "TEST FAILED: Wrong error message.\n{}".format(context.install_response['errorText']['message'])
    # assert type in context.install_response['errorText']['type'], "TEST FAILED: Node type expected: {}, Got: {}".format(type, context.install_response['errorText']['type'])
