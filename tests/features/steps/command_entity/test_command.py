import behave


@behave.when(u'Dataset is cloning')
def step_impl(context):
    context.clone_dataset = context.dataset.clone(clone_name="clone_dataset")


@behave.when(u'Dataset is cloning to existing dataset')
def step_impl(context):
    if not hasattr(context, 'filters'):
        context.filters = None
    context.clone_dataset = context.dataset.clone(dst_dataset_id=context.new_dataset.id, filters=context.filters)


@behave.then(u'Cloned dataset has "{item_count}" items')
def step_impl(context, item_count):
    pages = context.clone_dataset.items.list()
    assert pages.items_count == int(item_count), f"TEST FAILED: Expected {item_count}, Actual items in dataset {pages.items_count}"


@behave.when(u'Dataset is cloning with same name get already exist error')
def step_impl(context):
    try:
        context.clone_dataset = context.dataset.clone(clone_name=context.dataset.name)
    except context.dl.exceptions.FailedDependency as error:
        assert "Dataset with the same name already exists" in error.args[1], "TEST FAILED: Message not in error"
        assert context.dl.client_api.last_request.path_url.split('/')[-1] in error.args[
            1], "TEST FAILED: Command ID not in error"
        return
    assert False

@behave.then(u'command status is "{status}"')
def step_impl(context, status):
    assert context.command.status == status, f"TEST FAILED: Expected status {status}, Actual status {context.command.status}"


@behave.then(u'Validate faas command failed with error "{error}"')
def step_impl(context, error):
    assert context.command.status == 'failed', f"TEST FAILED: Expected status failed, Actual status {context.command.status}"
    assert error in context.command.error, f"TEST FAILED: Expected {error}, Actual {context.command.error}"

