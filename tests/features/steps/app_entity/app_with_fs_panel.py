import time
import random
from behave import given, when, then
import os
import json
import shutil
from datetime import datetime
from .. import fixtures


@given(u'I have an app with a filesystem panel in path "{filesystem_path}"')
@given(u'I have an app with a filesystem panel in path "{filesystem_path}" and remove key "{remove_key}"')
def step_impl(context, filesystem_path, remove_key=None):
    path = os.path.join(os.environ['DATALOOP_TEST_ASSETS'], filesystem_path)
    manifest_path = os.path.join(path, 'dataloop.json')
    # Need to set the original path and backup path in the context to restore the file later
    context.original_path = manifest_path
    context.backup_path = os.path.join(path, 'dataloop_backup.json')
    # Save the original dataloop.json file to restore it later
    if not os.path.exists(context.backup_path):
        shutil.copy(manifest_path, context.backup_path)
    with open(manifest_path, 'r') as file:
        manifest = json.load(file)
    manifest['name'] = f'filesystem-panel-{datetime.now().strftime("%M%S")}'
    if remove_key:
        fixtures.remove_key_from_nested_dict(manifest, remove_key)
    manifest['components']['computeConfigs'][0]['versions']['dtlpy'] = context.dl.__version__
    with open(manifest_path, 'w') as file:
        json.dump(manifest, file)

    context.dpk = context.project.dpks.publish(manifest_filepath=os.path.join(path, 'dataloop.json'), local_path=path)
    if hasattr(context.feature, 'dpks'):
        context.feature.dpks.append(context.dpk)
    else:
        context.feature.dpks = [context.dpk]

    context.app = context.project.apps.install(dpk=context.dpk)
    if hasattr(context.feature, 'apps'):
        context.feature.apps.append(context.app)
    else:
        context.feature.apps = [context.app]


@when(u'I fetch the panel')
def step_impl(context):
    url = context.app.routes[context.dpk.components.panels[0].name]
    context.url = url.split('v1')[1]


@then(u'I should find the sdk version from the computeConfig in the panel')
def step_impl(context):
    interval = 3
    num_tries = 300
    success = False
    url = context.app.routes[context.dpk.components.panels[0].name]
    url = url.split('v1')[1]

    while num_tries > 0 and not success:
        success, response = context.dl.client_api.gen_request(req_type='GET', path=url)
        if success:
            content = response.content.decode('utf-8')
            success = 'Panel({})'.format(context.dpk.components.compute_configs[0].versions['dtlpy']) in content
        if not success:
            time.sleep(interval)
            num_tries -= 1

    assert success, 'Failed to fetch panel'


@then(u'no services deployed in the project')
def step_impl(context):
    services = context.project.services.list()
    assert len(services.items) == 0, 'Services found in project'


@given(u'I update the panel with a new sdk version')
def step_impl(context):
    valid_sdk_versions = [v for v in ['1.102.14', '1.103.2', '1.104.0'] if v != context.dl.__version__]
    new_sdk_version = random.choice(valid_sdk_versions)

    path = os.path.join(os.environ['DATALOOP_TEST_ASSETS'], 'apps', 'filesystem_panel')
    manifest_path = os.path.join(path, 'dataloop.json')
    with open(manifest_path, 'r') as file:
        manifest = json.load(file)
    manifest['components']['computeConfigs'][0]['versions']['dtlpy'] = new_sdk_version
    with open(manifest_path, 'w') as file:
        json.dump(manifest, file)

    context.dpk = context.project.dpks.publish(manifest_filepath=os.path.join(path, 'dataloop.json'), local_path=path)
    context.app.dpk_version = context.dpk.version
    context.app.update()
    context.app = context.project.apps.get(app_id=context.app.id)
