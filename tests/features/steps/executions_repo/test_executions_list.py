import behave
from operator import attrgetter
import dtlpy as dl

@behave.when(u"I list service executions")
def step_impl(context):
    context.execution_list = context.service.executions.list()


@behave.then(u'I receive a list of "{count}" executions')
def step_impl(context, count):
    assert len(context.execution_list.items) == int(count)
    if int(count) > 0:
        for page in context.execution_list:
            for execution in page:
                assert isinstance(execution, context.dl.entities.Execution)


@behave.when(u'I create FAAS query filter with params')
def step_impl(context):
    """
    Search keywords : executions list with filter
    """
    context.filters = context.dl.Filters()

    params = dict()
    for row in context.table:
        if "id" in row['key'] or "name" in row['key'] or "Id" in row['key']:
            context.filters.add(field=row['key'], values=attrgetter(row['key'])(context))
        else:
            params[row['key']] = row['value']

    if params.get("resource"):
        context.filters.resource = params['resource']
    if params.get("updatedAt.gt"):
        context.filters.add(field="updatedAt", values=attrgetter(params['updatedAt.gt'])(context), operator=dl.FiltersOperations.GREATER_THAN)
    if params.get("updatedAt.lt"):
        context.filters.add(field="updatedAt", values=attrgetter(params['updatedAt.lt'])(context), operator=dl.FiltersOperations.LESS_THAN)


@behave.when(u"I list executions with filters")
def step_impl(context):
    context.execution_list = context.project.executions.list(filters=context.filters)


@behave.then(u'I validate pipeline executions params')
def step_impl(context):
    """
    Search keywords : pipeline executions list
    """
    filters = dl.Filters()
    filters.resource = "executions"
    filters.add(field="pipeline.id", values=context.pipeline.id)
    filters.sort_by(field='createdAt', value=dl.FiltersOrderByDirection.ASCENDING)
    index = 0
    for execution in context.project.executions.list(filters=filters).items:
        if ".id" in context.table[index]['value']:
            input_str = context.table[index]['value'].replace("item.id", context.item.id)
            input_str = input_str.replace("dataset.id", context.dataset.id)
        else:
            input_str = context.table[index]['value']
        expected_input = eval(input_str)
        execution_input = attrgetter(context.table[index]['key'])(execution)
        assert execution_input == expected_input, "TEST FAILED: Expected : {}, Actual got : {}".format(expected_input, execution_input)
        index += 1
