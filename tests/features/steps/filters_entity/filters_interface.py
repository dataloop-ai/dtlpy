import behave


@behave.given(u'I init Filters() using the given params')
def step_impl(context):
    context.resource = context.dl.FiltersResource.ITEM

    filters_resource_list = {
        "ITEM": context.dl.FiltersResource.ITEM,
        "ANNOTATION": context.dl.FiltersResource.ANNOTATION,
        "EXECUTION": context.dl.FiltersResource.EXECUTION,
        "PACKAGE": context.dl.FiltersResource.PACKAGE,
        "DPK": context.dl.FiltersResource.DPK,
        "APP": context.dl.FiltersResource.APP,
        "SERVICE": context.dl.FiltersResource.SERVICE,
        "TRIGGER": context.dl.FiltersResource.TRIGGER,
        "MODEL": context.dl.FiltersResource.MODEL,
        "WEBHOOK": context.dl.FiltersResource.WEBHOOK,
        "RECIPE": context.dl.FiltersResource.RECIPE,
        "DATASET": context.dl.FiltersResource.DATASET,
        "ONTOLOGY": context.dl.FiltersResource.ONTOLOGY,
        "TASK": context.dl.FiltersResource.TASK,
        "PIPELINE": context.dl.FiltersResource.PIPELINE,
        "PIPELINE_EXECUTION": context.dl.FiltersResource.PIPELINE_EXECUTION,
        "COMPOSITION": context.dl.FiltersResource.COMPOSITION,
        "FEATURE": context.dl.FiltersResource.FEATURE,
        "FEATURE_SET": context.dl.FiltersResource.FEATURE_SET,
        "ORGANIZATIONS": context.dl.FiltersResource.ORGANIZATIONS,
        "DRIVERS": context.dl.FiltersResource.DRIVERS,
        "SETTINGS": context.dl.FiltersResource.SETTINGS,
        "RESOURCE_EXECUTION": context.dl.FiltersResource.RESOURCE_EXECUTION
    }

    for parameter in context.table.rows:
        if parameter.cells[0] == "resource":
            context.resource = filters_resource_list[parameter.cells[1]]

    context.filters = context.dl.Filters(resource=context.resource)


@behave.when(u'I call Filters.add() using the given params')
def step_impl(context):
    context.field = None
    context.values = None
    context.operator = None
    context.method = None

    filters_operations_list = {
        "OR": context.dl.FiltersOperations.OR,
        "AND": context.dl.FiltersOperations.AND,
        "IN": context.dl.FiltersOperations.IN,
        "NOT_EQUAL": context.dl.FiltersOperations.NOT_EQUAL,
        "EQUAL": context.dl.FiltersOperations.EQUAL,
        "GREATER_THAN": context.dl.FiltersOperations.GREATER_THAN,
        "LESS_THAN": context.dl.FiltersOperations.LESS_THAN,
        "EXISTS": context.dl.FiltersOperations.EXISTS,
        "MATCH": context.dl.FiltersOperations.EXISTS
    }

    filters_method_list = {
        "OR": context.dl.FiltersMethod.OR,
        "AND": context.dl.FiltersMethod.AND,
    }

    for parameter in context.table.rows:
        if parameter.cells[0] == "field":
            context.field = parameter.cells[1]

        if parameter.cells[0] == "values":
            context.values = parameter.cells[1]

        if parameter.cells[0] == "operator":
            context.operator = filters_operations_list[parameter.cells[1]]

        if parameter.cells[0] == "method":
            context.method = filters_method_list[parameter.cells[1]]

    context.filters.add(
        field=context.field,
        values=context.values,
        operator=context.operator,
        method=context.method,
    )


@behave.when(u'I call Filters.add_join() using the given params')
def step_impl(context):
    context.field = None
    context.values = None
    context.operator = None
    context.method = context.dl.FiltersMethod.AND

    filters_operations_list = {
        "OR": context.dl.FiltersOperations.OR,
        "AND": context.dl.FiltersOperations.AND,
        "IN": context.dl.FiltersOperations.IN,
        "NOT_EQUAL": context.dl.FiltersOperations.NOT_EQUAL,
        "EQUAL": context.dl.FiltersOperations.EQUAL,
        "GREATER_THAN": context.dl.FiltersOperations.GREATER_THAN,
        "LESS_THAN": context.dl.FiltersOperations.LESS_THAN,
        "EXISTS": context.dl.FiltersOperations.EXISTS,
        "MATCH": context.dl.FiltersOperations.EXISTS
    }

    filters_method_list = {
        "OR": context.dl.FiltersMethod.OR,
        "AND": context.dl.FiltersMethod.AND,
    }

    for parameter in context.table.rows:
        if parameter.cells[0] == "field":
            context.field = parameter.cells[1]

        if parameter.cells[0] == "values":
            if parameter.cells[1] == "True":
                context.values = True
            elif parameter.cells[1] == "False":
                context.values = False
            else:
                context.values = parameter.cells[1]

        if parameter.cells[0] == "operator":
            context.operator = filters_operations_list[parameter.cells[1]]

        if parameter.cells[0] == "method":
            context.method = filters_method_list[parameter.cells[1]]

    context.filters.add_join(
        field=context.field,
        values=context.values,
        operator=context.operator,
        method=context.method,
    )


@behave.when(u'I call Filters.pop() using the given params')
def step_impl(context):
    context.field = None

    for parameter in context.table.rows:
        if parameter.cells[0] == "field":
            context.field = parameter.cells[1]

    context.filters.pop(
        field=context.field
    )


@behave.when(u'I call Filters.pop_join() using the given params')
def step_impl(context):
    context.field = None

    for parameter in context.table.rows:
        if parameter.cells[0] == "field":
            context.field = parameter.cells[1]

    context.filters.pop_join(
        field=context.field
    )


@behave.when(u'I call Filters.has_field() using the given params')
def step_impl(context):
    context.field = None

    for parameter in context.table.rows:
        if parameter.cells[0] == "field":
            context.field = parameter.cells[1]

    context.has_field_result = context.filters.has_field(
        field=context.field
    )


@behave.when(u'I call Filters.sort_by() using the given params')
def step_impl(context):
    context.field = None
    context.value = context.dl.FiltersOrderByDirection.ASCENDING

    filters_order_by_direction_list = {
        "DESCENDING": context.dl.FiltersOrderByDirection.DESCENDING,
        "ASCENDING": context.dl.FiltersOrderByDirection.ASCENDING
    }

    for parameter in context.table.rows:
        if parameter.cells[0] == "field":
            context.field = parameter.cells[1]

        if parameter.cells[0] == "value":
            context.value = filters_order_by_direction_list[parameter.cells[1]]

    context.filters.add(
        field=context.field,
        value=context.value,
    )


@behave.when(u'I call Filters.reset()')
def step_impl(context):
    context.filters.reset()
