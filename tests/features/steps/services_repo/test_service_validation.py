import behave


@behave.then(u'I validate service response params')
def step_impl(context):
    service_json = context.project.services.get(service_id=context.service.id).to_json()
    for row in context.table:
        assert service_json[row['key']] == row[
            'value'], f"TEST FAILED: Expected {row['value']}, Actual {service_json[row['key']]}"


@behave.when(u'set context.published_dpk to context.dpk')
def step_impl(context):
    context.dpk = context.published_dpk


@behave.then(u'service has app scope')
def step_impl(context):
    assert context.service.app[
               'id'] == context.app.id, f"TEST FAILED: app id is not as expected, expected: {context.app.id}, got: {context.service.app['id']}"
    assert context.service.app[
               'dpkId'] == context.dpk.base_id, f"TEST FAILED: dpk id is not as expected, expected: {context.dpk.base_id}, got: {context.service.app['dpkId']}"
    assert context.service.app[
               'dpkVersion'] == context.dpk.version, f"TEST FAILED: dpk version is not as expected, expected: {context.dpk.version}, got: {context.service.app['dpkVersion']}"
    assert context.service.app[
               'dpkName'] == context.dpk.name, f"TEST FAILED: dpk name is not as expected, expected: {context.dpk.name}, got: {context.service.app['dpkName']}"
