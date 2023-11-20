import behave


@behave.when(u'I update node in index "{index}" to start node')
def step_impl(context, index):
    context.pipeline.start_nodes.append({"nodeId": context.pipeline.nodes[int(index)].node_id,
                                         "type": "root"})

    try:
        context.pipeline = context.pipeline.update()
        context.error = None
    except Exception as e:
        context.error = e


@behave.when(u'I try to install pipeline in context')
def step_impl(context):
    try:
        context.pipeline = context.pipeline.install()
        context.error = None
    except Exception as e:
        context.error = e
