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
