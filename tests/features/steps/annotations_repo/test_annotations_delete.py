import behave


@behave.when(u'I delete a annotation x')
def step_impl(context):
    context.item.annotations.delete(annotation_id=context.annotation_x.id)


@behave.when(u'I try to delete a non-existing annotation')
def step_impl(context):
    try:
        context.project.datasets.delete(dataset_name='some_name',
                                        sure=True,
                                        really=True)
        context.error = None
    except Exception as e:
        context.error = e


@behave.then(u'No annotation was deleted')
def step_impl(context):
    context.annotations_list = context.item.annotations.list()
    assert len(context.annotations_list) == len(context.annotations)


@behave.then(u'Annotation x does not exist in item')
def step_impl(context):
    annotations_list = context.item.annotations.list()
    assert context.annotation_x not in annotations_list


@behave.given(u'I count other Annotation except "{annotation_type}" using "{entity}" entity')
def step_impl(context, annotation_type, entity):
    filters = context.dl.Filters(resource=context.dl.FiltersResource.ANNOTATION, field='type', values=annotation_type)
    if entity == 'dataset':
        annotations_list_filtered = context.dataset.annotations.list(filters=filters)
        annotations_list_all = context.dataset.annotations.list()
    elif entity == 'item':
        annotations_list_filtered = context.item.annotations.list(filters=filters)
        annotations_list_all = context.dataset.annotations.list()
    else:
        raise ValueError("Entity {} does not supported".format(entity))

    context.other_annotation_before_delete = len(annotations_list_all) - len(annotations_list_filtered)
    a = 5


@behave.when(u'I delete annotation from type "{annotation_type}" using "{entity}" entity')
def step_impl(context, annotation_type, entity):
    filters = context.dl.Filters(resource=context.dl.FiltersResource.ANNOTATION, field='type', values=annotation_type)
    if entity == 'dataset':
        context.dataset.annotations.delete(filters=filters)
    elif entity == 'item':
        context.item.annotations.delete(filters=filters)
    else:
        raise ValueError("Entity {} does not supported".format(entity))


@behave.then(u'I verify that I has the right number of annotations')
def step_impl(context):
    filters = context.dl.Filters(resource=context.dl.FiltersResource.ANNOTATION)
    annotations = context.dataset.annotations.list(filters=filters)
    assert len(annotations) == context.other_annotation_before_delete


@behave.when(u'I delete annotation')
def step_impl(context):
    context.annotation.delete()
