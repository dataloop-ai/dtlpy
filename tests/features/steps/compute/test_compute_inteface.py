import behave
import os
import json
from .. import fixtures
import shutil
import base64
from datetime import datetime


@behave.given(u'I fetch the compute from "{file_name}"')
@behave.given(u'I fetch the compute from "{file_name}" file and update compute with params "{params_flag}"')
def step_impl(context, file_name, params_flag='None'):
    assert params_flag in ['None', 'True', 'False'], \
        f"params_flag should be 'None', 'True' or 'False' but got {params_flag}"

    path = os.path.join(os.environ['DATALOOP_TEST_ASSETS'], file_name)
    with open(path, 'r') as file:
        context.json_object = json.load(file)

    # Need to set the original path and backup path in the context to restore the file later
    context.original_path = path
    context.backup_path = os.path.join(os.path.dirname(path), 'dataloop_backup.json')
    # Save the original dataloop.json file to restore it later
    if not os.path.exists(context.backup_path):
        shutil.copy(path, context.backup_path)

    context.json_object['config']['name'] = f"{context.json_object['config']['name']}-{datetime.now().strftime('%Y-%m-%d-%H-%M-%S')}"
    if eval(params_flag):
        params = dict()
        for row in context.table:
            params[row['key']] = row['value'] if row['value'] != 'None' else None
        fixtures.update_nested_dict(context.json_object, params)

    updated_text = json.dumps(context.json_object)
    encoded_text = base64.b64encode(updated_text.encode('utf-8'))

    with open(path, 'w') as file:
        file.write(encoded_text.decode('utf-8'))

