import behave


@behave.when(u'I add dependency to the dpk with params')
def step_impl(context):
    """
    This step is used to add one dependency to the dpk with all relevant attributes name , version etc.
    """
    params = dict()
    for row in context.table:
        try:
            value = eval(row['value'])
        except NameError:
            value = row['value']
        params.update({row['key']: value})

    # Add dependency to the dpk
    if not isinstance(context.dpk.dependencies, list):
        context.dpk.dependencies = list()
    context.dpk.dependencies.append(params)

    # Add the dependency name to the dpks_names list
    if not hasattr(context, 'dpks_names'):
        context.dpks_names = list()
    context.dpks_names.append({"name": params['name'], "flag": False})
