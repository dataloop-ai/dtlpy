import behave


@behave.when(u'I delete a dataset by the name of "{dataset_name}"')
def step_impl(context, dataset_name):
    context.project.datasets.delete(dataset_name=dataset_name,
                                    sure=True,
                                    really=True)


@behave.when(u'I delete a dataset by the id of the dataset "Dataset"')
def step_impl(context):
    context.project.datasets.delete(dataset_id=context.dataset.id,
                                    sure=True,
                                    really=True)


@behave.when(u'I try to delete a dataset by the name of "{dataset_name}"')
def step_impl(context, dataset_name):
    try:
        context.project.datasets.delete(dataset_name=dataset_name,
                                        sure=True,
                                        really=True)
        context.error = None
    except Exception as e:
        context.error = e


@behave.then(u'No dataset was deleted')
def step_impl(context):
    assert len(context.project.datasets.list()) == context.dataset_count
