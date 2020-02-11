from behave import fixture
from behave import use_fixture
import os
import json
import logging


@fixture
def after_feature(context, feature):
    if hasattr(feature, 'bot'):
        try:
            feature.bot.delete()
        except Exception:
            logging.exception('Failed to delete bot')

    if hasattr(feature, 'dataloop_feature_project'):
        try:
            feature.dataloop_feature_project.delete(True, True)
        except Exception:
            logging.exception('Failed to delete project')

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
        except Exception:
            logging.exception('Failed to update api calls')


@fixture
def after_tag(context, tag):
    
    if tag == 'services.delete':
        try:
            use_fixture(delete_services, context)
        except Exception:
            logging.exception('Failed to delete service')

    if tag == 'packages.delete':
        try:
            use_fixture(delete_packages, context)
        except Exception:
            logging.exception('Failed to delete package')

    if tag == 'packages.delete_one':
        try:
            use_fixture(delete_one_package, context)
        except Exception:
            logging.exception('Failed to delete package')

@fixture
def delete_packages(context):
    first_package_deleted = False
    if hasattr(context, 'first_package'):
        try:
            context.first_package.delete()
            first_package_deleted = True
        except Exception:
            pass

    if hasattr(context, 'second_package'):
        try:
            context.second_package.delete()
        except Exception:
            pass

    if not first_package_deleted and hasattr(context, 'package'):
        try:
            context.package.delete()
        except Exception:
            pass

@fixture
def delete_one_package(context):
    if hasattr(context, 'package'):
        try:
            context.package.delete()
        except Exception:
            pass

@fixture
def delete_services(context):
    first_service_deleted = False
    if hasattr(context, 'first_service'):
        try:
            context.first_service.delete()
            first_service_deleted = True
        except Exception:
            pass

    if hasattr(context, 'second_service'):
        try:
            context.second_service.delete()
        except Exception:
            pass

    if not first_service_deleted and hasattr(context, 'service'):
        try:
            context.service.delete()
        except Exception:
            pass
