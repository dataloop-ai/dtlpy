import behave
from .. import fixtures


@behave.when(u'I create a qa Task')
def step_impl(context):
    context.params = {param.split('=')[0]: fixtures.get_value(params=param.split('='), context=context) for param in
                      context.table.headings if
                      fixtures.get_value(params=param.split('='), context=context) is not None}
    context.params['task'] = context.task
    context.qa_task = context.dataset.tasks.create_qa_task(**context.params)


@behave.then(u'I receive a qa task object')
def step_impl(context):
    assert isinstance(context.qa_task, context.dl.entities.Task)


@behave.then(u'Qa task is properly made')
def step_impl(context):
    assert context.qa_task.name == '{}_qa'.format(context.task.name)
    assert context.qa_task.spec['type'] == 'qa'
