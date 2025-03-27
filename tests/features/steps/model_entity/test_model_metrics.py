import behave


@behave.when(u'I add metrics to the model')
def step_impl(context):
    context.model_metrics = context.dl.PlotSample(figure='loss',
                                                  legend='train',
                                                  x=0,
                                                  y=0.7974426797053585)

    context.model.metrics.create(samples=context.model_metrics, dataset_id=context.dataset.id)


@behave.then(u'I list model metrics and expect to "{num_metrics}"')
def step_impl(context, num_metrics):
    metrics = context.model.metrics.list().items
    assert len(metrics) == int(num_metrics), f"Expected number of metrics: {num_metrics}, Actual: {len(metrics)}"


@behave.then(u'I validate model metrics equal to context.model_metrics')
def step_impl(context):
    metrics = context.model.metrics.list().items
    assert metrics[0].to_json() == context.model_metrics.to_json(), \
        f"Expected metrics: {context.model_metrics.to_json()}, Actual: {metrics[0].to_json()}"
