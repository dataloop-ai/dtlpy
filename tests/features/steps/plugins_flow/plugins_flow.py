import behave
import json
import time
import os


@behave.when(u'I copy all relevant files from "{plugin_assets_path}" to "{plugin_directory_path}"')
def step_impl(context, plugin_assets_path, plugin_directory_path):
    plugin_assets_path = os.path.join(os.environ['DATALOOP_TEST_ASSETS'], plugin_assets_path)
    plugin_directory_path = os.path.join(os.environ['DATALOOP_TEST_ASSETS'], plugin_directory_path)

    # main.py
    assets_main_path = os.path.join(plugin_assets_path, 'main.py')
    plugin_main_path = os.path.join(plugin_directory_path, 'main.py')

    with open(assets_main_path, 'r') as f:
        main_text = f.read()

    with open(plugin_main_path, 'w') as f:
        f.write(main_text)

    # mock
    assets_mock_path = os.path.join(plugin_assets_path, 'mock.json')
    plugin_mock_path = os.path.join(plugin_directory_path, 'mock.json')

    with open(assets_mock_path, 'r') as f:
        assets_mock = json.load(f)

    assets_mock['inputs'][0]['value']['dataset_id'] = context.dataset.id
    assets_mock['inputs'][0]['value']['item_id'] = context.item.id

    with open(plugin_mock_path, 'w') as f:
        json.dump(assets_mock, f)

    # deployment.json
    assets_deployment_path = os.path.join(plugin_assets_path, 'deployment.json')
    plugin_deployment_path = os.path.join(plugin_directory_path, 'deployment.json')

    with open(assets_deployment_path, 'r') as f:
        assets_deployment = json.load(f)

    with open(plugin_deployment_path, 'w') as f:
        json.dump(assets_deployment, f)

    dataloop_dir = os.path.join(plugin_directory_path, '.dataloop')
    os.mkdir(dataloop_dir)
    state_json = os.path.join(dataloop_dir, 'state.json')
    with open(state_json, 'w') as f:
        json.dump(
            {
                "project": context.project.id
            },
            f
        )


@behave.when(u'I test local plugin in "{plugin_directory_path}"')
def step_impl(context, plugin_directory_path):
    plugin_directory_path = os.path.join(os.environ['DATALOOP_TEST_ASSETS'], plugin_directory_path)
    context.project.checkout()
    context.project.plugins.test_local_plugin(cwd=plugin_directory_path)


@behave.when(u'I push and deploy pluign in "{plugin_directory_path}"')
def step_impl(context, plugin_directory_path):
    plugin_directory_path = os.path.join(os.environ['DATALOOP_TEST_ASSETS'], plugin_directory_path)
    context.plugin = context.project.plugins.push(src_path=plugin_directory_path)
    context.deployment = context.project.deployments.deploy_from_local_folder(bot=context.bot_user,
                                                                              cwd=plugin_directory_path)
    time.sleep(30)


@behave.when(u'I upload item in "{item_path}" to dataset')
def step_impl(context, item_path):
    time.sleep(10)
    item_path = os.path.join(os.environ['DATALOOP_TEST_ASSETS'], item_path)
    context.uploaded_item_with_trigger = context.dataset.items.upload(local_path=item_path)


@behave.then(u'Item "{item_num}" annotations equal annotations in "{assets_annotations_path}"')
def step_impl(context, item_num, assets_annotations_path):
    num_try = 15
    assets_annotations_path = os.path.join(os.environ['DATALOOP_TEST_ASSETS'], assets_annotations_path)
    if item_num == '1':
        item = context.item
    else:
        item = context.uploaded_item_with_trigger

    with open(assets_annotations_path, 'r') as f:
        should_be_annotations = json.load(f)['annotations']

    # try to get annotations
    annotations = list()
    for i in range(num_try):
        annotations = item.annotations.list()
        if len(annotations) > 0:
            break
        else:
            time.sleep(10)

    assert len(annotations) == 1

    annotation = annotations[0]
    should_be_annotation = should_be_annotations[0]

    assert len(should_be_annotations) == 1
    assert annotation.label == should_be_annotation['label']
    assert annotation.coordinates == should_be_annotation['coordinates']
    assert annotation.type == should_be_annotation['type']
    assert annotation.attributes == should_be_annotation['attributes']
