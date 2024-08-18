import os
import time

import behave
import dtlpy
import random
import re


@behave.given(u'I create "{integration_type}" integration with name "{integration_name}"')
def step_impl(context, integration_type, integration_name):
    integration_options = {}
    if integration_type == 's3':
        integration_options["s3"] = eval(os.environ.get("aws"))
    elif integration_type == 'gcs':
        integration_options["gcs"] = {
            'key': None, 'secret': None, 'content': os.environ.get('gcs')
        }
    elif integration_type == 'azureblob':
        integration_options["azureblob"] = eval(os.environ.get("azureblob"))
    elif integration_type == 'aws-sts':
        integration_options["aws-sts"] = eval(os.environ.get("aws_sts"))
    elif integration_type == 'azuregen2':
        integration_options["azuregen2"] = eval(os.environ.get("azuregen2"))
    elif integration_type == 'key_value':
        integration_options["key_value"] = {
            'key': os.environ.get('key_value_key', 'default_key'),
            'value': os.environ.get('key_value_value', 'default_value')
        }
    elif integration_type == 'gcp-cross':
        integration_options["gcp-cross"] = {}

    assert integration_type in integration_options, "TEST FAILED: Wrong integration type: {}".format(integration_type)
    try:
        context.integration_type = integration_type

        if hasattr(context.feature, 'dataloop_feature_integration'):
            if context.feature.dataloop_feature_integration.type == integration_type and integration_name in context.feature.dataloop_feature_integration.name:
                context.integration = context.feature.dataloop_feature_integration
                return

        # Handle AzureDatalakeGen2 integration
        context.integration_type = context.integration_type.replace('azuregen2', 'azureblob')
        num = random.randint(1000, 10000)
        context.integration_name = f"{integration_name}-{num}"
        context.integration = context.project.integrations.create(
            integrations_type=context.integration_type,
            name=context.integration_name,
            options=integration_options[integration_type])
        context.feature.to_delete_integrations_ids.append(context.integration.id)
        context.feature.dataloop_feature_integration = context.integration
        context.error = None
    except Exception as e:
        context.error = e
        assert False, e


@behave.given(u'I create key value integration with key "{key}" value "{value}"')
def step_impl(context, key, value):
    integration_options = {
        'key': key, 'value': value
    }
    try:
        num = random.randint(1000, 10000)
        context.integration_name = f"{key}-{num}"
        context.integration = context.project.integrations.create(
            integrations_type=context.dl.IntegrationType.KEY_VALUE,
            name=context.integration_name,
            options=integration_options)
        context.feature.to_delete_integrations_ids.append(context.integration.id)
        context.feature.dataloop_feature_integration = context.integration
        context.error = None
    except Exception as e:
        context.error = e
        assert False, e


@behave.then(u'I validate integration with the name "{integration_name}" is created')
def step_impl(context, integration_name):
    try:
        context.integration = context.project.integrations.get(integrations_id=context.integration.id)
        context.error = None
    except Exception as e:
        context.error = e

    assert integration_name in context.integration.name, "TEST FAILED: Expected - {}, Got - {}".format(integration_name,
                                                                                                       context.integration.name)
    assert context.integration_type == context.integration.type, "TEST FAILED: Expected - {}, Got - {}".format(
        context.integration_type, context.integration.type)


@behave.when(u'I delete integration in context')
def step_impl(context):
    try:
        context.integration.delete(True, True)
        if context.feature.to_delete_integrations_ids:
            context.feature.to_delete_integrations_ids.pop(-1)
        context.error = None
    except Exception as e:
        context.error = e


@behave.then(u'I validate integration not in integrations list by context.integration_name')
def step_impl(context):
    assert context.integration_name not in [integration['name'] for integration in context.project.integrations.list()], \
        "TEST FAILED: Failed to delete integration: {}".format(context.integration_name)


@behave.then(u'I validate gcp-cross-project has correct service account pattern')
def step_impl(context):
    pattern = r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$"
    time.sleep(5)
    context.integration = context.project.integrations.get(context.integration.id)

    dataloop_service_account = False
    for metadata_obj in context.integration.metadata:
        if metadata_obj['name'] == "email":
            dataloop_service_account = bool(re.match(pattern, metadata_obj['value']))
            break

    assert dataloop_service_account, f"TEST FAILED: Not found service account , \nIntegration metadata: {context.integration.metadata}"
