from __future__ import print_function
from behave import fixture
from behave import use_fixture
import os
import json


@fixture
def after_feature(context, feature):
    if hasattr(feature, 'dataloop_feature_project'):
        try:
            feature.dataloop_feature_project.delete(True, True)
        except:
            pass

    # update api call json
    if hasattr(feature, 'dataloop_feature_dl'):
        try:
            api_calls_path = os.path.join(os.environ['DATALOOP_TEST_ASSETS'], 'api_calls.json')
            with open(api_calls_path, 'r') as f:
                api_calls = json.load(f)
            if context.feature.name in api_calls:
                api_calls[context.feature.name] += feature.dataloop_feature_dl.client_api.calls_counter.number
            else:
                api_calls[context.feature.name] = feature.dataloop_feature_dl.client_api.calls_counter.number
            with open(api_calls_path, 'w') as f:
                json.dump(api_calls, f)
        except:
            pass

@fixture
def after_tag(context, tag):
    if tag == 'plugins.delete':
        try:
            use_fixture(delete_plugins, context)
        except:
            pass

@fixture
def delete_plugins(context):
    if hasattr(context, 'first_plugin'):
        context.first_plugin.delete()

    if hasattr(context, 'second_plugin'):
        context.second_plugin.delete()