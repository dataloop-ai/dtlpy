import behave


@behave.when(u"I init code bases with params: project, dataset, client_api")
def step_impl(context):
    context.codebases = context.dl.repositories.Codebases(
        project=context.project,
        dataset=context.dataset,
        client_api=context.dataset.items._client_api
    )


@behave.when(u"I init code bases with params: project, client_api")
def step_impl(context):
    context.codebases = context.dl.repositories.Codebases(
        project=context.project,
        client_api=context.dataset.items._client_api
    )


@behave.then(u'I receive a code bases repository object')
def step_impl(context):
    assert isinstance(context.codebases, context.dl.repositories.Codebases)


@behave.when(u'I try to init code bases with params: client_api')
def step_impl(context):
    try:
        context.codebases = context.dl.repositories.Codebases(
            client_api=context.dataset.items._client_api
        )
        context.error = None
    except Exception as e:
        context.error = e


@behave.when(u"I init code bases with params: dataset, client_api")
def step_impl(context):
    context.codebases = context.dl.repositories.Codebases(
        dataset=context.dataset,
        client_api=context.dataset.items._client_api
    )


@behave.then(u'Codebases project are equal')
def step_impl(context):
    assert context.project.to_json() == context.codebases.project.to_json()


@behave.then(u'Codebases dataset equal "Dataset"')
def step_impl(context):
    assert context.dataset.to_json() == context.codebases.dataset.to_json()


@behave.then(u'Codebases dataset has name "{name}"')
def step_impl(context, name):
    assert context.codebases.dataset.name == name
