import dtlpy as dl
import behave
import time


@behave.when(u'I create a pipeline with 2 dataset nodes and trigger with filters')
def step_impl(context):
    params = dict()
    for row in context.table:
        params[row['key']] = row['value']

    t = time.localtime()
    current_time = time.strftime("%H-%M-%S", t)
    context.pipeline_name = 'pipeline-{}'.format(current_time)

    context.pipeline = context.project.pipelines.create(name=context.pipeline_name, project_id=context.project.id)

    dataset_node_1 = dl.DatasetNode(
        name="datsset-1",
        project_id=context.project.id,
        dataset_id=context.dataset.id,
        dataset_folder="/pipeline",
        position=(1, 1)
    )

    dataset_node_2 = dl.DatasetNode(
        name="dataset-2",
        project_id=context.project.id,
        dataset_id=context.dataset.id,
        position=(2, 2),
        dataset_folder='/'
    )

    context.pipeline.nodes.add(dataset_node_1).connect(node=dataset_node_2)
    if params:  # Test delivered filters for trigger
        filters = dl.Filters()
        for key, val in params.items():
            filters.add(field=key, values=val)

        dataset_node_1.add_trigger(filters=filters)
    else:
        dataset_node_1.add_trigger()

    context.pipeline = context.pipeline.update()
    context.pipeline.install()

    time.sleep(5)


@behave.then(u'pipeline trigger created with filter params')
def step_impl(context):
    context.triggers = context.pipeline.triggers.list()[0][0].filters.get("$and")  # Get list of dictionaries
    context.triggers_keys = dict((key, dict_object[key]) for dict_object in context.triggers for key in dict_object).keys()

    row = context.table.headings[0]
    for val in row.split(', '):
        assert val.strip() in context.triggers_keys, "TEST FAILED: Missing {} in trigger filters\n{}".format(val.strip(), context.triggers_keys)
