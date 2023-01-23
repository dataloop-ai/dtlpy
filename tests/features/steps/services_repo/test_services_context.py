import os
import random

import behave
import dtlpy as dl


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
