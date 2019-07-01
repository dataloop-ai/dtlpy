import behave


@behave.given(u"I remove annotations attributes")
def step_impl(context):
    context.annotations_get = context.item.annotations.list()
    for annotation in context.annotations_get:
        annotation.attributes = list()


@behave.when(u"I update annotations")
def step_impl(context):
    context.item.annotations.update(
        annotations=context.annotations_get.annotations,
        system_metadata=True,
    )


@behave.then(u"Item annotations has no attributes")
def step_impl(context):
    annotations_get = context.item.annotations.list()
    for annotation in annotations_get:
        assert annotation.attributes == list()


@behave.given(u"I change annotations attributes to non-existing attributes")
def step_impl(context):
    context.annotations_get = context.item.annotations.list()
    for annotation in context.annotations_get:
        annotation.attributes = ["some_attribute_name"]


@behave.given(u'I change all annotations types to "{type_name}"')
def step_impl(context, type_name):
    context.annotations_get = context.item.annotations.list()
    for annotation in context.annotations_get:
        annotation.type = type_name


@behave.then(u'All item annotations have type "{type_name}"')
def step_impl(context, type_name):
    annotations_get = context.item.annotations.list()
    for annotation in annotations_get:
        assert annotation.type == type_name


@behave.given(u'I change all annotations labels to "{label_name}"')
def step_impl(context, label_name):
    context.annotations_get = context.item.annotations.list()
    for annotation in context.annotations_get:
        annotation.label = label_name


@behave.then(u'All item annotations have label "{label_name}"')
def step_impl(context, label_name):
    annotations_get = context.item.annotations.list()
    for annotation in annotations_get:
        assert annotation.label == label_name


@behave.when(u"I try to update annotations")
def step_impl(context):
    annotation_ids = list()
    for annotation in context.annotations_get:
        annotation_ids.append(annotation.id)
    try:
        context.item.annotations.update(
            annotations=context.annotations_get,
            annotations_ids=annotation_ids,
            system_metadata=True,
        )
        context.error = None
    except Exception as e:
        context.error = e


@behave.given(u"I change annotation values")
def step_impl(context):
    context.annotation_x.attributes = list()
    context.annotation_x.label = "person"


@behave.when(u"I update annotation")
def step_impl(context):
    context.item.annotations.update(
        annotations=context.annotation_x,
        system_metadata=True,
    )


@behave.then(u"Annotation should be updateed")
def step_impl(context):
    annotation_get = context.item.annotations.get(context.annotation_x.id)
    assert annotation_get.attributes == list()
    assert annotation_get.label == "person"


@behave.given(u'I add "{rais_valuse}" to annotation coordinates')
def step_impl(context, rais_valuse):
    context.annotation_x.top += 50
    context.annotation_x.right += 50
    context.annotation_x.left += 50
    context.annotation_x.bottom += 50


@behave.then(u'annotation x coordinates should be changed accordingly')
def step_impl(context):
    annotation_get = context.item.annotations.get(context.annotation_x.id)
    assert annotation_get.coordinates == context.annotation_x.coordinates
