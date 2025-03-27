import os
import random

import behave
import dtlpy as dl
import time


@behave.given(u'I append package to packages')
def step_impl(context):
    if not hasattr(context, "packages"):
        context.packages = list()
    context.packages.append(context.package)


@behave.when(u'I get the service from project number {project_index}')
def step_impl(context, project_index):
    context.service = context.projects[int(project_index) - 1].services.get(service_id=context.service.id)


@behave.when(u'I get the service from package number {project_index}')
def step_impl(context, project_index):
    context.service = context.packages[int(project_index) - 1].services.get(service_id=context.service.id)


@behave.then(u'Service Project_id is equal to project {project_index} id')
def step_impl(context, project_index):
    assert context.service.project_id == context.projects[int(project_index) - 1].id


@behave.then(u'Service Project.id is equal to project {project_index} id')
def step_impl(context, project_index):
    assert context.service.project.id == context.projects[int(project_index) - 1].id


@behave.then(u'Service Package_id is equal to package {project_index} id')
def step_impl(context, project_index):
    assert context.service.package_id == context.packages[int(project_index) - 1].id


@behave.then(u'Service Package.id is equal to package {project_index} id')
def step_impl(context, project_index):
    assert context.service.package.id == context.packages[int(project_index) - 1].id


@behave.when(u'I deploy a service with init prams')
def step_impl(context):
    context.service = context.project.services.deploy(
        service_name=context.package.name,
        package=context.package,
        module_name=context.package.modules[0].name,
        init_input={
            'item': context.item.id,
            'ds': context.dataset.id,
            'string': 'test'
        }
    )

    context.to_delete_services_ids.append(context.service.id)


@behave.then(u'service has integrations')
def step_impl(context):
    assert len(context.service.integrations) > 0


@behave.then(u'I execute the service')
def step_impl(context):
    context.execution: dl.Execution = context.service.execute(item_id=context.item.id,
                                                              function_name='run',
                                                              project_id=context.project.id,
                                                              sync=True,
                                                              return_output=False,
                                                              stream_logs=False
                                                              )


@behave.then(u'The execution success with the right output')
def step_impl(context):
    assert context.execution.output == {
        'item_id': context.item.id,
        'string': 'test',
        'dataset': context.dataset.id
    }


@behave.when(u'I execute service on "{input}" with type "{input_type}" with name "{name_input}"')
def step_impl(context, input, input_type, name_input):
    if input.isdigit():
        input = eval(input)
    try:
        context.execution: dl.Execution = context.service.execute(project_id=context.project.id,
                                                                  execution_input=dl.FunctionIO(type=input_type,
                                                                                                value=input,
                                                                                                name=name_input)
                                                                  )
        context.error = None
    except Exception as e:
        context.error = e
        return True

    num_try = 40
    interval = 10
    finished = False

    for i in range(num_try):
        time.sleep(interval)
        status = context.execution.get_latest_status()
        if status['status'] in ['success', 'failed']:
            if "error" in status.keys():
                context.error = dl.exceptions.PlatformException
                context.error.message = status['error']
            finished = True
            break

    assert finished, f"TEST FAILED: Execution status - {status}"


@behave.Then(u'Services are created with expected configuration')
def atp_step_impl(context):
    # Extract configurations from service and dpk
    dpk_runtime = context.json_object['components']['computeConfigs'][0]['runtime']
    service_runtime = context.project.services.list().items[0].runtime

    # Convert service_runtime object to a dictionary
    service_runtime_dict = vars(service_runtime)

    # Mapping of fields between dpk_runtime and service_runtime (handle naming differences)
    field_mapping = {
        'numReplicas': 'num_replicas',
        'concurrency': 'concurrency',
        'podType': 'pod_type',
        'runnerImage': 'runner_image'
    }

    # Prepare filtered dicts based on the mapping
    dpk_filtered = {}
    service_filtered = {}

    for dpk_field, service_field in field_mapping.items():
        if dpk_field in dpk_runtime and service_field in service_runtime_dict:
            dpk_value = dpk_runtime[dpk_field]
            service_value = service_runtime_dict[service_field]

            if dpk_field == 'podType':
                dpk_value = str(dpk_value).split('.')[-1].lower().replace('_', '-')
                service_value = service_value.lower().replace('_', '-')

            # Add the filtered values
            dpk_filtered[dpk_field] = dpk_value
            service_filtered[dpk_field] = service_value

    # Compare the filtered configurations
    assert dpk_filtered == service_filtered, f"Configurations do not match:\nDPK Runtime: {dpk_filtered}\nService Runtime: {service_filtered}"
