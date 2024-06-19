import behave
import dtlpy as dl


@behave.when(u'I add a code node to the pipeline')
def step_impl(context):
    def run(item, string):
        item.metadata['user'] = {'userInput': string}
        item.update()
        return item

    context.new_node = dl.CodeNode(
        name='codeNode',
        position=(4, 4),
        project_id=context.project.id,
        method=run,
        project_name=context.project.name
    )

    context.pipeline.nodes.add(node=context.new_node)
    context.pipeline.update()


@behave.when(u'I execute the pipeline batch items')
def step_impl(context):
    context.command = context.pipeline.execute_batch(
        execution_inputs=dl.FunctionIO(type=dl.PackageInputType.STRING, value='test', name='string'),
        filters=dl.Filters(field='dir', values='/test', context={'datasets': [context.dataset.id]}))


@behave.when(u'I get the pipeline service')
def step_impl(context):
    service_name = context.pipeline.nodes[0].namespace.service_name
    context.service = dl.services.get(service_name=service_name)


@behave.when(u'I execute the service batch items')
def step_impl(context):
    context.command = context.service.execute_batch(
        execution_inputs=dl.FunctionIO(type=dl.PackageInputType.STRING, value='test', name='string'),
        filters=dl.Filters(field='dir', values='/test', context={'datasets': [context.dataset.id]}))


@behave.then(u'pipeline execution are success in "{items_count}" items')
def step_impl(context, items_count):
    assert context.command.status == dl.ExecutionStatus.SUCCESS
    assert len(context.command.spec['inputs']) == eval(items_count)
    assert context.pipeline.pipeline_executions.list().items_count == eval(items_count)


@behave.then(u'service execution are success in "{items_count}" items')
def step_impl(context, items_count):
    assert context.command.status == dl.ExecutionStatus.SUCCESS
    assert len(context.command.spec['inputs']) == eval(items_count)
    assert context.service.executions.list().items_count == eval(items_count)
