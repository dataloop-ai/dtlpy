import behave


@behave.when(u'I update annotation label with new name "{label_name}"')
@behave.then(u'I update annotation label with new name "{label_name}"')
def step_impl(context, label_name):
    context.annotation.label = label_name
    context.annotation.update(system_metadata=True)
    assert context.annotation.item.annotations.get(annotation_id=context.annotation.id).label in [label_name, "Edited"]

