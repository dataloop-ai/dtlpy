import uuid
import dtlpy as dl
import behave
import random
import os
import json


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


def check_no_connection_for_input(pipeline_json, node_input):
    connections = [connection['src']['portId'] for connection in pipeline_json['connections']]
    # If portId in connection return False
    if node_input['portId'] in connections:
        return False
    return True


def generate_pipeline_json(context, pipeline_json):
    pipeline_json['name'] = 'json-pipe-{}'.format(random.randrange(10000, 100000))
    pipeline_json['creator'] = context.dl.info()['user_email']
    pipeline_json['projectId'] = context.project.id
    pipeline_json['orgId'] = context.project.org['id']

    for node in pipeline_json.get('nodes', []):
        node['projectId'] = context.project.id

    datasets_node = [node for node in pipeline_json.get('nodes', []) if node['type'] == 'storage']
    if not hasattr(context, "datasets"):
        for node in datasets_node:
            node['name'] = context.dataset.name
            node['metadata']["datasetId"] = context.dataset.id
    else:
        for index in range(len(datasets_node)):
            datasets_node[index]['name'] = context.datasets[index].name
            datasets_node[index]['metadata']["datasetId"] = context.datasets[index].id

    task_nodes = [node for node in pipeline_json.get('nodes', []) if node['type'] == 'task']
    for node in task_nodes:
        node['projectId'] = context.project.id
        if not hasattr(context, "datasets"):
            node['metadata']["recipeTitle"] = context.dataset.recipes.list()[0].title
            node['metadata']["recipeId"] = context.dataset.recipes.list()[0].id
            node['metadata']["datasetId"] = context.dataset.id
        else:
            node['metadata']["recipeTitle"] = context.datasets[0].recipes.list()[0].title
            node['metadata']["recipeId"] = context.datasets[0].recipes.list()[0].id
            node['metadata']["datasetId"] = context.datasets[0].id
        node['metadata']["taskOwner"] = context.dl.info()['user_email']
        node['metadata']["workload"] = [
            {
                "assigneeId": context.dl.info()['user_email'],
                "load": 100
            }
        ]

    function_nodes = [node for node in pipeline_json.get('nodes', []) if node['type'] == 'function']
    for node in function_nodes:
        node['namespace']['serviceName'] = context.service.name
        node['namespace']['packageName'] = context.package.name
        node['namespace']['projectName'] = context.project.name

    ml_nodes = [node for node in pipeline_json.get('nodes', []) if node['type'] == 'ml']
    for node in ml_nodes:
        node['namespace']['projectName'] = context.project.name
        if node['namespace']['functionName'] == "train" and check_no_connection_for_input(pipeline_json, node['inputs'][0]):
            node['inputs'][0]['defaultValue'] = context.model.id
        elif node['namespace']['functionName'] == "predict":
            node['name'] = context.model.name
            node['metadata']["modelId"] = context.model.id
            node['metadata']["modelName"] = context.model.name
        elif node['namespace']['functionName'] == "evaluate":
            for node_input in node['inputs']:
                if node_input['type'] == 'Model' and check_no_connection_for_input(pipeline_json, node_input):
                    node_input['defaultValue'] = context.model.id
                elif node_input['type'] == 'Dataset' and check_no_connection_for_input(pipeline_json, node_input):
                    node_input['defaultValue'] = context.dataset.id

    custom_nodes = [node for node in pipeline_json.get('nodes', []) if node['type'] == 'custom']
    for node in custom_nodes:
        node['namespace']['projectName'] = context.project.name
        node['namespace']['packageName'] = context.dpk.name
        node['projectId'] = context.project.id
        node['dpkName'] = context.dpk.name
        node['appName'] = context.dpk.display_name

    variables = pipeline_json.get('variables', []) if pipeline_json.get('variables', []) else []
    for variable in variables:
        if variable['type'] == "Model":
            variable['value'] = context.model.id
        elif variable['type'] == "Dataset":
            variable['value'] = context.dataset.id

    return pipeline_json


@behave.given(u'I create pipeline from json in path "{path}"')
def step_impl(context, path):
    test_path = os.path.join(os.environ['DATALOOP_TEST_ASSETS'], path)
    with open(test_path, 'r') as pipeline_path:
        pipeline_json = json.load(pipeline_path)

    pipeline_payload = generate_pipeline_json(
        context=context,
        pipeline_json=pipeline_json
    )

    try:
        context.pipeline = context.project.pipelines.create(pipeline_json=pipeline_payload, project_id=context.project.id)
        context.to_delete_pipelines_ids.append(context.pipeline.id)
        for node in pipeline_json['nodes']:
            if node['type'] == 'task':
                context.task_name = node['name']
        context.error = None
    except Exception as e:
        context.error = e
