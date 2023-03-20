import os
import behave
import json


@behave.when(u'I create "{integration_type}" integration with name "{integration_name}"')
def step_impl(context, integration_type, integration_name):
    integration_options = {
        "aws": eval(os.environ.get("aws")),
        "gcs": {
            'key': None, 'secret': None, 'content': os.environ.get('gcs')
        },
        "azureblob": eval(os.environ.get("azureblob"))
        ,
        "aws_sts": eval(os.environ.get("aws_sts")),
        "key_value": {
            'key': os.environ.get('key_value_key', 'default_key'), 'value': os.environ.get('key_value_value', 'default_value')
        }
    }
    assert integration_type in integration_options, "TEST FAILED: Wrong integration type: {}".format(integration_type)
    try:
        # Handle AWS integration
        context.integration_type = integration_type.replace('aws', 's3')

        context.integration = context.project.integrations.create(
            integrations_type=context.integration_type,
            name=integration_name,
            options=integration_options[integration_type])
        context.to_delete_integrations_ids.append(context.integration.id)
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

    assert integration_name == context.integration.name, "TEST FAILED: Expected - {}, Got - {}".format(integration_name, context.integration.name)
    assert context.integration_type == context.integration.type, "TEST FAILED: Expected - {}, Got - {}".format(context.integration_type, context.integration.type)


@behave.when(u'I delete integration in context')
def step_impl(context):
    try:
        context.integration.delete(True, True)
        context.error = None
    except Exception as e:
        context.error = e


@behave.then(u'I validate integration "{integration_name}" not in integrations list')
def step_impl(context, integration_name):
    assert integration_name not in [integration['name'] for integration in context.project.integrations.list()], \
        "TEST FAILED: Failed to delete integration: {}".format(integration_name)
