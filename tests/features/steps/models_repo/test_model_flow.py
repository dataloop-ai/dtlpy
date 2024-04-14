import json
import time
import random

import behave
import dtlpy as dl
import os


@behave.when(u'I create a dummy model package by the name of "{package_name}" with entry point "{entry_point}"')
def step_impl(context, package_name, entry_point):
    if package_name == "ac-lr-package":
        context.codebase_local_dir = os.path.join(os.environ["DATALOOP_TEST_ASSETS"], 'model_ac_lr')
    else:
        context.codebase_local_dir = os.path.join(os.environ["DATALOOP_TEST_ASSETS"], 'models_flow')
    module = dl.PackageModule.from_entry_point(
        entry_point=os.path.join(context.codebase_local_dir, entry_point))
    context.dpk.components.modules._dict[0] = module.to_json()
    context.codebase = context.project.codebases.pack(
        directory=context.codebase_local_dir,
        name=package_name,
        description="some description"
    )
    context.dpk.codebase = context.codebase
    context.dpk.components.modules[0].entry_point = entry_point
    context.dpk.name = f"to_delete_{package_name}_{str(random.randrange(0, 1000))}"
    context.dpk.display_name = f"to_delete_{package_name}_{str(random.randrange(0, 1000))}"

    context.dpk.components.compute_configs._dict[0] = {
        "name": "default",
        "versions": {"dtlpy": dl.__version__},
        'runtime': dl.KubernetesRuntime(
            runner_image='jjanzic/docker-python3-opencv',
            pod_type=dl.InstanceCatalog.REGULAR_XS,
            autoscaler=dl.KubernetesRabbitmqAutoscaler(
                min_replicas=1,
                max_replicas=1),
            concurrency=1).to_json()
    }


@behave.when(u'I create a model from package by the name of "{model_name}" with status "{status}" in index "{index}"')
def step_impl(context, model_name, status, index):
    model = {
        'name': model_name,
        'description': 'model for testing',
        'datasetId': context.dataset.id,
        'moduleName': context.dpk.components.modules[0].name,
        'scope': 'project',
        'model_artifacts': [dl.LinkArtifact(
            url='https://storage.googleapis.com/model-mgmt-snapshots/ResNet50/model.pth',
            filename='model.pth').to_json()],
        'status': status,
        'configuration': {'weights_filename': 'model.pth',
                          'batch_size': 16,
                          'num_epochs': 10},
        'labels': [label.tag for label in context.dataset.labels],
        'metadata': {'system': {'subsets': {'train': dl.Filters().prepare(),
                                            'validation': dl.Filters().prepare()}}},
        'outputType': dl.AnnotationType.BOX,
    }
    if int(index) == 0:
        context.dpk.components.models[int(index)].update(model)
    else:
        context.dpk.components.models.append(model)


@behave.when(u'i fetch the model by the name "{model_name}"')
def step_impl(context, model_name):
    context.model = context.project.models.get(model_name=model_name)


@behave.when(u'I "{func}" the model')
@behave.when(u'I "{func}" the model with exception "{flag}"')
def step_impl(context, func, flag=None):
    context.model = dl.models.get(model_id=context.model.id)
    try:
        if func == 'evaluate':
            service_config = None
            if hasattr(context, "service_config"):
                service_config = context.service_config
            context.execution = context.model.evaluate(dataset_id=context.dataset.id, filters=dl.Filters(),
                                                       service_config=service_config)
            context.to_delete_services_ids.append(context.execution.service_id)
        else:
            context.execution = context.model.__getattribute__(func)()
        context.error = None
    except Exception as e:
        # If flag is None, Test should be failed and raise error
        if not flag:
            raise e
        context.error = e


@behave.when(u'i train the model with init param model none')
def step_impl(context):
    try:
        context.execution = context.model.train(service_config={"initParams": {"model_entity": None}})
    except Exception as e:
        context.error = e


@behave.when(u'i predict the model on the item id "{item_id}"')
def step_impl(context, item_id):
    try:
        context.execution = context.model.predict(item_id)
    except Exception as e:
        context.error = e


@behave.then(u'model status should be "{status}" with execution "{flag}" that has function "{func}"')
def step_impl(context, status, flag, func):
    num_try = 45
    interval = 20
    completed = False

    if eval(flag):
        if isinstance(context.execution, dl.Execution):
            for i in range(num_try):
                time.sleep(interval)
                context.execution = dl.executions.get(execution_id=context.execution.id)
                assert context.execution.function_name == func
                if context.execution.latest_status['status'] in ['success', 'failed']:
                    completed = True
                    break
    else:
        time.sleep(10)
        completed = True
    assert completed, f"TEST FAILED: execution was not completed, after {round(num_try * interval / 60, 1)} minutes"

    context.model = dl.models.get(model_id=context.model.id)
    assert context.model.status == status, f"TEST FAILED: model status is not as expected, expected: {status}, got: {context.model.status}"


@behave.then(u'model status should be "{status}"')
def step_impl(context, status):
    assert context.model_clone.status == status, f"TEST FAILED: model status is not as expected, expected: {status}, got: {context.model_clone.status}"


@behave.then(u'Dataset has a scores file')
def step_impl(context):
    model_csv_filename = f'{context.model.id}.csv'
    model_json_filename = f'{context.model.id}-interpolated.json'
    filters = dl.Filters(field='hidden', values=True)
    filters.add(field='name', values=[model_csv_filename, model_json_filename], operator=dl.FiltersOperations.IN)
    items = context.dataset.items.list(filters=filters)
    assert items.items_count != 0, f'Found {items.items_count} items with name {model_csv_filename}.'


@behave.when(u'i call the precision recall api')
def step_impl(context):
    payload = {
        'datasetId': context.dataset.id,
        'confThreshold': 0,
        'iouThreshold': 0.3,
        'metric': 'accuracy',
        'modelId': context.model.id,
    }
    success, response = dl.client_api.gen_request(req_type="post",
                                                  path=f"/ml/metrics/precisionRecall",
                                                  json_req=payload)
    assert success, f'Failed to call precision recall api, response: {response}'
    context.response = response.json()


@behave.then(u'i should get a json response')
def step_impl(context):
    assert isinstance(context.response, dict), f'Failed to call precision recall api, response: {context.response}'
    with open(os.path.join(os.environ["DATALOOP_TEST_ASSETS"], 'models_flow', 'precisionrecall.json'), 'r') as f:
        expected_output = json.load(f)

    assert context.response == expected_output, f'results are not as expected, expected: {expected_output}, got: {context.response}'
    assert len(context.response['recall']) == 202 and len(context.response[
                                                              'precision']) == 202, f'points are not as expected, expected: 201, got: {len(context.response["recall"])}'


@behave.given(u'I upload "{item_num}" box annotation to item')
@behave.when(u'I upload "{item_num}" box annotation to item')
def step_impl(context, item_num):
    builder = context.item.annotations.builder()
    item_num = int(item_num)
    for i in range(item_num):
        builder.add(annotation_definition=dl.Box(top=i * 10, left=i * 10, bottom=i * 20, right=i * 20, label=str(i)))
    context.item.annotations.upload(builder)


@behave.then(u'Log "{log_message}" is in model.log() with operation "{operation}"')
def step_impl(context, log_message, operation):
    num_tries = 60
    interval_time = 5
    success = False

    for i in range(num_tries):
        time.sleep(interval_time)
        for log in context.model.log(view=False, model_operation=operation):
            if log_message in log:
                success = True
                break
        if success:
            break

    assert success, f"TEST FAILED: after {round(num_tries * interval_time / 60, 1)} minutes"


@behave.then(u'service metadata has a model id and operation "{operation}"')
def step_impl(context, operation):
    context.service = dl.services.get(service_id=context.execution.service_id)
    assert context.service.metadata.get('ml', {}).get(
        'modelId') == context.model.id, f"TEST FAILED: model id is not in service metadata"
    assert context.service.metadata.get('ml', {}).get(
        'modelOperation') == operation, f"TEST FAILED: model operation is not in service metadata"


@behave.when(u'I add service_config to context from dpk model configuration')
def step_impl(context):
    context.service_config = context.dpk.components.models[0]['metadata']['system']['ml']['serviceConfig']
    context.service_config['versions'] = {"dtlpy": dl.__version__}


@behave.when(u'i add a Service config runtime')
def step_impl(context):
    context.service_config = {'runtime': {}}
    params = context.table.headings
    for row in params:
        row = row.split('=')
        context.service_config['runtime'][row[0]] = row[1]


@behave.then(u'check service runtime')
def step_impl(context):
    service = dl.services.get(service_id=context.execution.service_id).to_json()
    params = context.table.headings
    for row in params:
        row = row.split('=')
        assert service['runtime'][row[0]] == row[
            1], f"TEST FAILED: service runtime is not as expected, expected: {row[1]}, got: {service['runtime'][row[0]]}"


@behave.then(u'i have a model service')
def step_impl(context):
    context.service = context.model.services.list().items[0]
    assert context.service is not None, f"TEST FAILED: service is not in model services"
    assert context.service.metadata.get('ml', {}).get(
        'modelId') == context.model.id, f"TEST FAILED: model id is not in service metadata"


@behave.when(u'I update the model variable in pipeline to reference to this model')
def step_impl(context):
    context.pipeline.variables[0].value = context.model.id
    context.pipeline = context.pipeline.update()


@behave.then(u'the model service id updated')
def step_impl(context):
    service = context.model.services.list().items[0]
    assert service is not None, f"TEST FAILED: service is not in model services"
    assert service.id == context.service.id, f"TEST FAILED: service id is not as expected, expected: {context.service.id}, got: {service.id}"
    assert service.metadata.get('ml', {}).get(
        'modelId') == context.model.id, f"TEST FAILED: model id is not in service metadata"


@behave.when(u'i add service id "{service_id}" to model metadata')
def step_impl(context, service_id):
    context.model = dl.models.get(model_id=context.model.id)
    context.model.metadata['system']['deploy']['services'].append(service_id)
    context.model = context.model.update(True)


@behave.when(u'I delete model')
@behave.then(u'I delete model')
def step_impl(context):
    context.model.delete()


@behave.then(u'model is deleted')
def step_impl(context):
    try:
        context.model = dl.models.get(model_id=context.model.id)
        assert False, "TEST FAILED: model is not deleted"
    except:
        pass


@behave.then(u'model metadata should include operation "{operation}" with filed "{field}" and length "{value}"')
def step_impl(context, operation, field, value):
    value = int(value)
    context.model = dl.models.get(model_id=context.model.id)
    assert operation in context.model.metadata['system'], f"TEST FAILED: operation {operation} is not in model metadata"
    assert field in context.model.metadata['system'][operation], f"TEST FAILED: field {field} is not in model metadata"
    assert len(context.model.metadata['system'][operation][
                   field]) == value, f"TEST FAILED: field {field} length is not as expected, expected: {value}, got: {len(context.model.metadata['system'][operation][field])}"


@behave.when(u'i clone a model')
def step_impl(context):
    context.model = context.model.clone(
        model_name='clone_model',
        project_id=context.model.project_id,
        dataset=dl.datasets.get(dataset_id=context.model.dataset_id),
        status='created'
    )


@behave.then(u'model input should be equal "{input}", and output should be equal "{output}"')
def step_impl(context, input, output):
    assert context.model.input_type == input, f"TEST FAILED: model input is not as expected, expected: {input}, got: {context.model.input}"
    assert context.model.output_type == output, f"TEST FAILED: model output is not as expected, expected: {output}, got: {context.model.output}"


@behave.then(u'model do not have operation "{operation}"')
def step_impl(context, operation):
    assert operation not in context.model.metadata.get('system',
                                                       {}), f"TEST FAILED: operation {operation} is in model metadata"


@behave.then(u'models with the names "{models_name}" status "{model_status}"')
def step_impl(context, models_name, model_status):
    names = models_name.split(",")

    for model in context.project.models.list().items:
        if model.name in names:
            assert model.status == model_status, f"TEST FAILED: model {model.id} status is not as expected, expected: {model_status}, got: {model.status}"


@behave.when(u'I remove attributes "{values}" from dpk model in index "{index}"')
def step_impl(context, values, index=0):
    model = context.dpk.components.models[int(index)]
    values = values.split(",")
    for value in values:
        if "metadata" in value:
            if "system" in value:
                del model['metadata']['system'][value.split('.')[-1]]
            else:
                del model['metadata'][value.split('.')[-1]]
        else:
            del model[value]
