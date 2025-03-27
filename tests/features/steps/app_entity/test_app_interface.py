import behave


@behave.when(u'I create a context.custom_installation var')
def step_impl(context):
    if hasattr(context, "dpk"):
        context.custom_installation = {"components": context.dpk.to_json().get("components", {}),
                                       "dependencies": context.dpk.to_json().get("dependencies", [])}
    else:
        raise AttributeError("'dpk' not found in 'context'")


@behave.when(u'I create template from pipeline app')
def step_impl(context):
    success, response = context.dl.client_api.gen_request(req_type='post',
                                                          path=f"/apps/{context.app.id}/resolvePipelineTemplate",
                                                          json_req={})

    if success:
        context.pipeline = context.dl.Pipeline.from_json(client_api=context.dl.client_api,
                                                         _json=response.json(),
                                                         project=context.project)
        context.to_delete_pipelines_ids.append(context.pipeline.id)
    else:
        raise context.dl.exceptions.PlatformException(response)


@behave.then(u'App is not installed in the project')
def step_impl(context):
    try:
        app = context.project.apps.get(app_name=context.dpk.display_name)
        error = f"TEST FAILED: able to get app: {app.id} - {app.name}"
    except Exception:
        error = None

    assert error is None, error
