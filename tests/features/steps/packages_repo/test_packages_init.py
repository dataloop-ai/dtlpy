import behave


@behave.when(u"I init packages with params: project, dataset, client_api")
def step_impl(context):
    context.packages = context.dl.repositories.Packages(
        project=context.project,
        dataset=context.dataset,
        client_api=context.dataset.items._client_api
    )


@behave.when(u"I init packages with params: project, client_api")
def step_impl(context):
    context.packages = context.dl.repositories.Packages(
        project=context.project,
        client_api=context.dataset.items._client_api
    )


@behave.then(u'I receive a packages repository object')
def step_impl(context):
    assert isinstance(context.packages, context.dl.repositories.Packages)


@behave.when(u'I try to init packages with params: client_api')
def step_impl(context):
    try:
        context.packages = context.dl.repositories.Packages(
            client_api=context.dataset.items._client_api
        )
        context.error = None
    except Exception as e:
        context.error = e


@behave.when(u"I init packages with params: dataset, client_api")
def step_impl(context):
    context.packages = context.dl.repositories.Packages(
        dataset=context.dataset,
        client_api=context.dataset.items._client_api
    )


@behave.then(u'Packages project are equal')
def step_impl(context):
    assert context.project.to_json() == context.packages.project.to_json()


@behave.then(u'Packages dataset equal "Dataset"')
def step_impl(context):
    assert context.dataset.to_json() == context.packages.dataset.to_json()


@behave.then(u'Packages dataset has name "{name}"')
def step_impl(context, name):
    assert context.packages.dataset.name == name
