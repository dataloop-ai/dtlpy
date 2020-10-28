import behave


@behave.given(u'I append item to Items')
def step_impl(context):
    if not hasattr(context, "items"):
        context.items = list()
    context.items.append(context.item)


@behave.when(u'I get the annotation from item number {item_index}')
def step_impl(context, item_index):
    context.annotation = context.items[int(item_index) - 1].annotations.get(annotation_id=context.annotation.id)


@behave.when(u'I get the annotation from dataset number {dataset_index}')
def step_impl(context, dataset_index):
    context.annotation = context.datasets[int(dataset_index) - 1].annotations.get(annotation_id=context.annotation.id)


@behave.then(u'Annotation dataset_id is equal to dataset {dataset_index} id')
def step_impl(context, dataset_index):
    assert context.annotation.dataset_id == context.datasets[int(dataset_index)-1].id


@behave.then(u'Annotation dataset.id is equal to dataset {dataset_index} id')
def step_impl(context, dataset_index):
    assert context.annotation.dataset.id == context.datasets[int(dataset_index)-1].id


@behave.then(u'Annotation item_id is equal to item {item_index} id')
def step_impl(context, item_index):
    assert context.annotation.item_id == context.items[int(item_index)-1].id


@behave.then(u'Annotation item.id is equal to item {item_index} id')
def step_impl(context, item_index):
    assert context.annotation.item.id == context.items[int(item_index)-1].id
