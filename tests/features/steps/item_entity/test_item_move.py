import behave


@behave.given(u'I have directory with the name "{directory}"')
def step_impl(context, directory):
    context.dataset.items.make_dir(directory=directory)


@behave.when(u'I move the item to "{new_path}"')
def step_impl(context, new_path):
    context.item.move(new_path=new_path)


@behave.then(u'I insure that new full name is "{filename}"')
def step_impl(context, filename):
    assert context.item.filename == filename
