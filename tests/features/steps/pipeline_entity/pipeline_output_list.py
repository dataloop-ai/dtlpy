import dtlpy as dl
import behave
import time


@behave.when(u'I create a pipeline with code and task node')
def step_impl(context):
    context.pipeline = context.project.pipelines.create(name='sdk-pipeline-test', project_id=context.project.id)

    def run(item):
        dataset = item.dataset
        items = []
        for page in dataset.items.list():
            for item in page:
                items.append(item.id)

        return items

    code_node = dl.CodeNode(
        name='My Function',
        position=(1, 1),
        project_id=context.project.id,
        method=run,
        project_name=context.project.name,
        outputs=[dl.PipelineNodeIO(input_type=dl.PackageInputType.ITEMS,
                                   name='items',
                                   display_name='items',
                                   action='item')]
    )

    task_node = dl.TaskNode(
        name='My Task',
        recipe_id=context.recipe.id,
        recipe_title=context.recipe.title,
        task_owner=dl.info()['user_email'],
        workload=[dl.WorkloadUnit(assignee_id=dl.info()['user_email'], load=100)],
        position=(2, 3),
        project_id=context.project.id,
        dataset_id=context.dataset.id,
    )

    context.pipeline.nodes.add(node=code_node).connect(node=task_node,source_port=code_node.outputs[0])
    filters = dl.Filters(field='datasetId', values=context.dataset.id)
    code_node.add_trigger(filters=filters)
    context.pipeline.update()
    context.pipeline.install()
    context.to_delete_pipelines_ids.append(context.pipeline.id)


@behave.then(u'verify pipeline output result of "{total_items}" items')
def step_impl(context, total_items):
    task = context.project.tasks.list()[0]
    num_try = 60
    interval = 10
    finished = False

    for i in range(num_try):
        time.sleep(interval)
        print("Waited Sec : {}".format(interval * (i + 1)))
        if task.get_items().items_count == int(total_items):
            print("{} is ready".format(task.name))
            finished = True
            break

    assert finished