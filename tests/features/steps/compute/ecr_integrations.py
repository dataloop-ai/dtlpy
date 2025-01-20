import os
import time
from behave import given, when, then
import random
import string

@given(u'There are no private registry integrations in the organization')
def step_impl(context):
    context.org = context.dl.organizations.get(organization_id=context.project.org['id'])
    integrations = context.org.integrations.list()
    for integration in integrations:
        if integration['type'] == context.dl.IntegrationType.PRIVATE_REGISTRY:
            integration = context.org.integrations.get(integrations_id=integration['id'])
            integration.delete(sure=True, really=True)


@given(u'A deployed service with custom docker image from "{type}" private registry')
def step_impl(context, type):
    image_name = ''
    if type == 'ECR':
        image_name = "636666312771.dkr.ecr.eu-west-1.amazonaws.com/aharon:latest"
    elif type == 'GAR':
        image_name = "europe-docker.pkg.dev/viewo-g/faas-test/zvi/from-ecr:latest"

    def run(item):
        return item

    context.service = context.project.services.deploy(
        name=f'{type}-service-' + ''.join(random.choices(string.ascii_lowercase + string.digits, k=5)) + 'a',
        func=run,
        runtime=context.dl.KubernetesRuntime(
            runner_image=image_name,
            autoscaler=None,
            num_replicas=1
        )
    )

@given(u'I execute the service')
def step_impl(context):
    context.execution = context.service.execute(execution_input={"item": context.item.id})

@then(u'I should get an ImagePullBackOff error')
def step_impl(context):
    start = time.time()
    timeout = 60 * 5
    success = False
    while time.time() - start < timeout:
        time.sleep(5)
        context.execution = context.project.executions.get(execution_id=context.execution.id)
        success = context.execution.latest_status['status'] == 'created'
        status = context.service.status()
        relevant_statuses = [s for s in status['runtimeStatus'] if s['createdAt'].split('.')[0] >= context.service.updated_at.split('.')[0]]
        has_image_pull_back_off = False
        for s in relevant_statuses:
            success = success and s['status'] == False
            has_image_pull_back_off = s['reason'] in ['ErrImagePull', 'ImagePullBackOff']

        success = success and has_image_pull_back_off
        if success:
            break

    assert success, 'ImagePullBackOff error was not received'

@when(u'I create an ECR integration')
def step_impl(context):
    context.org = context.dl.organizations.get(organization_id=context.project.org['id'])
    context.integration = context.org.integrations.create(
        integrations_type='private-registry',
        name='ecr-1',
        metadata={"provider": "aws"},
        options={
            "name": "AWS",
            "spec": {
                "accessKeyId": os.environ['ECR_ACCESS_KEY_ID'],
                "secretAccessKey": os.environ['ECR_SECRET_ACCESS_KEY'],
                "account": os.environ['ECR_ACCOUNT'],
                "region": "eu-west-1",
            }
        }
    )


@when(u'I create an GAR integration')
def step_impl(context):
    context.org = context.dl.organizations.get(organization_id=context.project.org['id'])
    context.integration = context.org.integrations._create_private_registry_gar(service_account=os.environ['GAR_SERVICE_ACCOUNT_JSON'], location=os.environ['GAR_LOCATION'])


@when(u'I pause and resume the service')
def step_impl(context):
    context.service.pause()
    context.service = context.project.services.get(service_id=context.service.id)
    context.service.resume()
    context.service = context.project.services.get(service_id=context.service.id)

@then(u'The execution should complete successfully')
def step_impl(context):
    start = time.time()
    timeout = 60 * 5
    success = False
    while time.time() - start < timeout:
        time.sleep(5)
        context.execution = context.project.executions.get(execution_id=context.execution.id)
        success = context.execution.latest_status['status'] == 'success'
        if success:
            break

    assert success, 'Execution did not complete successfully'

@when(u'I delete the context integration')
def step_impl(context):
    context.integration.delete(sure=True, really=True)