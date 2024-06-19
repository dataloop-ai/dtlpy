import time
import behave
import dtlpy as dl


@behave.when(u'I build a pipeline with dynamic node status')
def step_impl(context):
    context.pipeline = context.project.pipelines.create(name='test_pipeline', project_id=context.project.id)

    def run(item):
        item.metadata['user'] = {'userInput': 'test'}
        item = item.update()
        return item

    context.root = dl.CodeNode(
        name='root',
        position=(2, 2),
        project_id=context.project.id,
        method=run,
        project_name=context.project.name
    )

    def run1(item):
        if item.metadata.get('user', {}).get('userInput', None):
            item.metadata['user']['userInput'] = None
            item = item.update()
            raise ValueError("err")
        return item

    context.n1 = dl.CodeNode(
        name='n1',
        position=(3, 2),
        project_id=context.project.id,
        method=run1,
        project_name=context.project.name
    )

    context.n2 = dl.DatasetNode(
        name='n2',
        position=(4, 2),
        project_id=context.project.id,
        dataset_id=context.dataset.id
    )

    context.t1 = dl.DatasetNode(
        name='t1',
        position=(2, 3),
        project_id=context.project.id,
        dataset_id=context.dataset.id
    )

    context.t2 = dl.DatasetNode(
        name='t2',
        position=(2, 4),
        project_id=context.project.id,
        dataset_id=context.dataset.id
    )

    context.pipeline.nodes.add(node=context.root).connect(node=context.n1).connect(node=context.n2)
    context.pipeline.nodes.add(node=context.t1).connect(node=context.n1)
    context.pipeline.nodes.add(node=context.t2).connect(node=context.n1)
    context.t1.add_trigger()
    context.t2.add_trigger(actions=dl.TriggerAction.CREATED,
                           filters=dl.Filters(field='metadata.user.userInput', values=['test']))
    context.pipeline.update()
    context.pipeline.install()
    context.to_delete_pipelines_ids.append(context.pipeline.id)


@behave.when(u'rerun the cycle from the beginning')
def step_impl(context):
    dl.pipeline_executions.rerun(
        pipeline_id=context.pipeline.id,
        method=dl.CycleRerunMethod.START_FROM_BEGINNING
    )


@behave.when(u'rerun the cycle from the execution')
def step_impl(context):
    dl.pipeline_executions.rerun(
        pipeline_id=context.pipeline.id,
        method=dl.CycleRerunMethod.START_FROM_BEGINNING,
        filters=dl.Filters(resource=dl.FiltersResource.EXECUTION),
    )


@behave.when(u'rerun the cycle from the "{node_pos}" node')
def step_impl(context, node_pos):
    dl.pipeline_executions.rerun(
        pipeline_id=context.pipeline.id,
        method=dl.CycleRerunMethod.START_FROM_NODES,
        start_nodes_ids=[context.pipeline.nodes[int(node_pos) - 1].node_id]
    )


@behave.then(u'Cycle completed with save "{save}"')
def step_impl(context, save):
    time.sleep(2)

    num_try = 60
    interval = 10
    completed = 0
    cycles = []

    for i in range(num_try):
        completed = 0
        time.sleep(interval)
        pipeline: dl.Pipeline = context.pipeline
        cycles = pipeline.pipeline_executions.list().items
        if eval(save):
            context.cycles = cycles
        for cycle in cycles:
            if cycle.status == 'success' or cycle.status == 'failed':
                completed += 1
        if completed == len(cycles):
            break
        if i + 1 % 5 == 0:
            # Print the cycle URL every 5 intervals
            context.dl.logger.info(f"Cycle URL : {pipeline.url}/executions/{cycle.id}")
        context.dl.logger.info("Step is running for {:.2f}[s] and now Going to sleep {:.2f}[s]".format((i + 1) * interval, interval))

    assert completed > 0 and len(cycles), "TEST FAILED: cycle was not completed"


@behave.when(u'rerun the cycle from the failed node')
def step_impl(context):
    dl.pipeline_executions.rerun(
        pipeline_id=context.pipeline.id,
        method=dl.CycleRerunMethod.START_FROM_FAILED_EXECUTIONS,
    )


@behave.then(u'the pipeline cycle should be rerun')
def step_impl(context):
    pipeline = dl.pipelines.get(pipeline_id=context.pipeline.id)
    pipeline_cycle = pipeline.pipeline_executions.list().items
    assert len(pipeline_cycle) == len(context.cycles), 'pipeline cycle amount should be equal to the amount of cycles'
    for cycle in pipeline_cycle:
        for old_cycle in context.cycles:
            if cycle.id == old_cycle.id:
                if cycle.executions != old_cycle.executions:
                    return True
    context.cycles = pipeline_cycle
    assert False, 'pipeline cycle should be rerun'


@behave.then(u'the pipeline cycle should not change')
def step_impl(context):
    pipeline = dl.pipelines.get(pipeline_id=context.pipeline.id)
    pipeline_cycle = pipeline.pipeline_executions.list().items
    assert len(pipeline_cycle) == len(context.cycles), 'pipeline cycle amount should be equal to the amount of cycles'
    for cycle in pipeline_cycle:
        for old_cycle in context.cycles:
            if cycle.id == old_cycle.id:
                if cycle.executions != old_cycle.executions:
                    assert False, 'pipeline cycle should not be rerun'
    return True


@behave.when(u'pipeline many to one')
def step_impl(context):
    context.pipeline = context.project.pipelines.create(name='test_pipeline-many-to-one', project_id=context.project.id)

    def run(item):
        item.metadata['user'] = {'userInput': 'test'}
        item = item.update()
        return item

    context.root = dl.CodeNode(
        name='root',
        position=(2, 2),
        project_id=context.project.id,
        method=run,
        project_name=context.project.name
    )

    def run1(item):
        if item.metadata.get('user', {}).get('userInput', None):
            item.metadata['user']['userInput'] = None
            item = item.update()
            raise ValueError("err")
        return item

    context.n1 = dl.CodeNode(
        name='n1',
        position=(3, 2),
        project_id=context.project.id,
        method=run1,
        project_name=context.project.name
    )

    context.n2 = dl.DatasetNode(
        name='n2',
        position=(4, 2),
        project_id=context.project.id,
        dataset_id=context.dataset.id
    )

    context.t1 = dl.DatasetNode(
        name='t1',
        position=(2, 3),
        project_id=context.project.id,
        dataset_id=context.dataset.id
    )

    context.t2 = dl.DatasetNode(
        name='t2',
        position=(2, 4),
        project_id=context.project.id,
        dataset_id=context.dataset.id
    )

    context.pipeline.nodes.add(node=context.root).connect(node=context.n1).connect(node=context.n2)
    context.pipeline.nodes.add(node=context.t1).connect(node=context.n1)
    context.pipeline.nodes.add(node=context.t2).connect(node=context.n1)
    context.t1.add_trigger()
    context.t2.add_trigger(actions=dl.TriggerAction.CREATED,
                           filters=dl.Filters(field='metadata.user.userInput', values=['test']))
    context.pipeline.update()
    context.pipeline.install()
    context.to_delete_pipelines_ids.append(context.pipeline.id)


@behave.when(u'Cycle status should be "{status}"')
def step_impl(context, status):
    time.sleep(20)
    cycle = context.pipeline.pipeline_executions.list().items[0]
    assert cycle.status == status, f'Cycle status should be {status}'
