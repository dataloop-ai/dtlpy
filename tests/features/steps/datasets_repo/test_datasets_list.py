import behave


@behave.when(u'I list all datasets')
def step_impl(context):
    context.dataset_list = context.project.datasets.list()


@behave.then(u'I receive an empty datasets list')
def step_impl(context):
    assert len(context.dataset_list) == 0


@behave.given(u'I careat a dataset by the name of "{dataset_name}"')
def step_impl(context, dataset_name):
    context.dataset = context.project.datasets.create(dataset_name=dataset_name)
    context.dataset_count += 1


@behave.then(u'I receive a datasets list of "{dataset_count}" dataset')
def step_impl(context, dataset_count):
    assert len(context.dataset_list) == int(dataset_count)


@behave.then(u'The dataset in the list equals the dataset I created')
def step_impl(context):
    assert context.dataset.to_json() == context.dataset_list[0].to_json()
