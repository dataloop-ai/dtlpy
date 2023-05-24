import behave


@behave.when(u'Dataset is cloning')
def step_impl(context):
    context.clone_dataset = context.dataset.clone(clone_name="clone_dataset")


@behave.then(u'Cloned dataset has "{item_count}" items')
def step_impl(context, item_count):
    pages = context.dataset.items.list()
    assert pages.items_count == int(item_count)


@behave.when(u'Dataset is cloning with same name get already exist error')
def step_impl(context):
    try:
        context.clone_dataset = context.dataset.clone(clone_name=context.dataset.name)
    except context.dl.exceptions.FailedDependency as error:
        assert "Dataset with the same name already exists" in error.args[1], "TEST FAILED: Message not in error"
        assert context.dl.client_api.last_request.path_url.split('/')[-1] in error.args[1], "TEST FAILED: Command ID not in error"
        return
    assert False
