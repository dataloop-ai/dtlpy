import uuid

import dtlpy as dl
import behave
import random


@behave.given(u'I create "{node_type}" node with params')
def step_impl(context, node_type):
    params = dict()
    for row in context.table:
        params[row['key']] = row['value']

    if node_type == "dataset":
        context.node = dl.DatasetNode(
            name=params.get('name', context.dataset.name),
            project_id=context.project.id,
            dataset_id=params.get('dataset_id', context.dataset.id),
            dataset_folder=params.get('folder', None),
            position=eval(params.get('position', "(1, 1)"))
        )

    elif node_type == 'code':
        def run(item):
            return item

        context.node = dl.CodeNode(
            name=params.get('name', "codenode"),
            position=eval(params.get('position', "(1, 1)")),
            project_id=context.project.id,
            method=run,
            project_name=context.project.name,
            inputs=[dl.PipelineNodeIO(port_id=str(uuid.uuid4()),
                                      input_type=params.get('input_type', "Item"),
                                      name=params.get('input_name', "Item"),
                                      color=None,
                                      display_name=params.get('input_display_name', "Item"),
                                      actions=None if not params.get('input_actions') else params.get('input_actions').split(','))],
            outputs=[dl.PipelineNodeIO(port_id=str(uuid.uuid4()),
                                       input_type=params.get('output_type', "Item"),
                                       name=params.get('output_name', "Item"),
                                       color=None,
                                       display_name=params.get('output_display_name', "Item"),
                                       actions=None if not params.get('output_actions') else params.get('output_actions').split(','))]

        )
    elif node_type == 'task':
        context.task_name = params.get('name', "My Task")
        context.node = dl.TaskNode(
            name=context.task_name,
            recipe_id=context.recipe.id,
            recipe_title=context.recipe.title,
            task_owner=params.get('taskOwner', dl.info()['user_email']),
            workload=[dl.WorkloadUnit(assignee_id=params.get('assigneeId', dl.info()['user_email']), load=100)],
            position=eval(params.get('position', "(1, 1)")),
            task_type=params.get('type', "annotation"),
            project_id=context.project.id,
            dataset_id=context.dataset.id,
            repeatable=eval(params.get("repeatable", "True"))
        )

    context.nodes.append(context.node)


@behave.Given(u'I create pipeline with the name "{pipeline_name}"')
def step_impl(context, pipeline_name):
    context.pipeline_name = f'{pipeline_name}-{random.randrange(1000, 10000)}'
    context.pipeline = context.project.pipelines.create(name=context.pipeline_name, project_id=context.project.id)
    context.to_delete_pipelines_ids.append(context.pipeline.id)


@behave.when(u'I add and connect all nodes in list to pipeline entity')
def step_impl(context):
    assert context.nodes, "TEST FAILED: Nodes list is empty.{}".format(context.nodes)

    context.pipeline.nodes.add(context.nodes[0])
    context.nodes.pop(0)

    for i in range(len(context.nodes)):
        context.pipeline.nodes[i].connect(context.nodes[i])

    try:
        context.pipeline = context.pipeline.update()
        context.error = None
    except Exception as e:
        context.error = e


@behave.when(u'I add trigger to first node with params')
def step_impl(context):
    params = dict()
    for row in context.table:
        params[row['key']] = row['value']

    context.filters = context.dl.Filters()
    for key, val in params.items():
        context.filters.add(field=key, values=eval(val))

    context.pipeline.nodes[0].add_trigger(filters=context.filters)
    context.pipeline = context.pipeline.update()


@behave.when(u'I update pipeline attributes with params')
def step_impl(context):
    context.pipeline = context.pipeline.pipelines.get(pipeline_id=context.pipeline.id)
    for row in context.table:
        att = f"context.pipeline.{row['key']}"
        val = f"'{row['value']}'"
        exec(f"{att} = {val}")

    context.pipeline = context.pipeline.update()


@behave.when(u'I get pipeline in context by id')
def step_impl(context):
    context.pipeline = context.pipeline.pipelines.get(pipeline_id=context.pipeline.id)


@behave.then(u'I validate pipeline attributes with params')
def step_impl(context):
    for row in context.table:
        att = f"context.pipeline.{row['key']}"
        val = f"'{row['value']}'"
        exec(f"assert {att} == {val}, 'TEST FAILED: Expected '+{val}+', Actual '+{att}")


@behave.when(u'I add action "{action}" to connection in index "{num}"')
def step_impl(context, action, num):
    context.pipeline.connections[int(num)].action = action

    try:
        context.pipeline = context.pipeline.update()
        context.error = None
    except Exception as e:
        context.error = e


@behave.when(u'I add all nodes in list to pipeline entity')
def step_impl(context):
    assert context.nodes, "TEST FAILED: Nodes list is empty.{}".format(context.nodes)

    for i in range(len(context.nodes)):
        context.pipeline.nodes.add(context.nodes[i])

    try:
        context.pipeline = context.pipeline.update()
        context.error = None
    except Exception as e:
        context.error = e


@behave.when(u'I update pipeline context.node "{att}" with "{val}"')
def step_imp(context, att, val):
    setattr(context.node, att, eval(val))
    context.pipeline.update()
