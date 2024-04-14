import behave
import dtlpy as dl


@behave.when('I delete the org')
def step_impl(context):
    success, response = context.dl.client_api.gen_request(path="/orgs/{}".format(context.org.id), req_type="DELETE")
    assert response.status_code == 500
    res = response.json()
    context.error = res['message']


@behave.given(u'I update the project org')
@behave.when(u'I update the project org')
def step_impl(context):
    if context.org is None:
        raise Exception('context.org is not defined')

    payload = {"org_id": context.org.id}
    success, response = context.dl.client_api.gen_request(req_type='patch', path='/projects/' + context.project.id + '/org',
                                                    data=payload)
    if not success:
        raise dl.exceptions.PlatformException(response)

    context.project = dl.projects.get(project_id=context.project.id)