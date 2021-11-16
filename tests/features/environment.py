from behave import fixture
from behave import use_fixture
import os
import json
import logging
from filelock import FileLock


@fixture
def after_feature(context, feature):
    if hasattr(feature, 'bot'):
        try:
            feature.bot.delete()
        except Exception:
            logging.exception('Failed to delete bot')

    if hasattr(feature, 'dataloop_feature_project'):
        try:
            if 'frozen_dataset' in feature.tags:
                fix_project_with_frozen_datasets(project=feature.dataloop_feature_project)
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
            # lock the file for multi processes needs
            with FileLock("api_calls.json.lock"):
                with open(api_calls_path, 'w') as f:
                    json.dump(api_calls, f)
        except Exception:
            logging.exception('Failed to update api calls')


def fix_project_with_frozen_datasets(project):
    datasets = project.datasets.list()
    for dataset in datasets:
        if dataset.readonly:
            dataset.set_readonly(False)


@fixture
def after_tag(context, tag):
    if tag == 'services.delete':
        try:
            use_fixture(delete_services, context)
        except Exception:
            logging.exception('Failed to delete service')
    elif tag == 'packages.delete':
        try:
            use_fixture(delete_packages, context)
        except Exception:
            logging.exception('Failed to delete package')
    elif tag == 'pipelines.delete':
        try:
            use_fixture(delete_pipeline, context)
        except Exception:
            logging.exception('Failed to delete package')
    elif tag == 'feature_set.delete':
        try:
            use_fixture(delete_feature_set, context)
        except Exception:
            logging.exception('Failed to delete feature set')
    elif tag == 'feature.delete':
        try:
            use_fixture(delete_feature, context)
        except Exception:
            logging.exception('Failed to delete feature set')
    elif tag == 'bot.create':
        try:
            use_fixture(delete_bots, context)
        except Exception:
            logging.exception('Failed to delete bots')
    elif tag == 'second_project.delete':
        try:
            use_fixture(delete_second_project, context)
        except Exception:
            logging.exception('Failed to delete second project')
    elif tag == 'converter.platform_dataset.delete':
        try:
            use_fixture(delete_converter_dataset, context)
        except Exception:
            logging.exception('Failed to delete converter dataset')
    elif tag == 'frozen_dataset':
        pass
    elif 'testrail-C' in tag:
        pass
    else:
        raise ValueError('unknown tag: {}'.format(tag))


@fixture
def delete_second_project(context):
    if hasattr(context, 'second_project'):
        context.second_project.delete(True, True)


@fixture
def delete_bots(context):
    if not hasattr(context, 'to_delete_projects_ids'):
        return

    all_deleted = True
    while context.to_delete_projects_ids:
        project_id = context.to_delete_projects_ids.pop(0)
        try:
            project = context.dl.projects.get(project_id=project_id)
            for bot in project.bots.list():
                try:
                    bot.delete()
                except:
                    logging.exception('Failed deleting bots: ')
                    all_deleted = False
                    pass
        except context.dl.exceptions.NotFound:
            pass
        except:
            logging.exception('Failed deleting bots: ')
    assert all_deleted


@fixture
def delete_packages(context):
    if not hasattr(context, 'to_delete_packages_ids'):
        return

    all_deleted = True
    while context.to_delete_packages_ids:
        package_id = context.to_delete_packages_ids.pop(0)
        try:
            context.dl.packages.delete(package_id=package_id)
        except context.dl.exceptions.NotFound:
            pass
        except:
            all_deleted = False
            logging.exception('Failed deleting package: ')
    assert all_deleted


@fixture
def delete_feature_set(context):
    if not hasattr(context, 'to_delete_feature_set_ids'):
        return

    all_deleted = True
    while context.to_delete_feature_set_ids:
        feature_set = context.to_delete_feature_set_ids.pop(0)
        try:
            context.dl.feature_sets.delete(feature_set_id=feature_set)
        except context.dl.exceptions.NotFound:
            pass
        except:
            all_deleted = False
            logging.exception('Failed deleting feature_set: ')
    assert all_deleted


@fixture
def delete_feature(context):
    if not hasattr(context, 'to_delete_feature_ids'):
        return

    all_deleted = True
    while context.to_delete_feature_ids:
        feature = context.to_delete_feature_ids.pop(0)
        try:
            context.dl.feature.delete(feature_id=feature)
        except context.dl.exceptions.NotFound:
            pass
        except:
            all_deleted = False
            logging.exception('Failed deleting feature: ')
    assert all_deleted


@fixture
def delete_pipeline(context):
    if not hasattr(context, 'to_delete_pipelines_ids'):
        return

    all_deleted = True
    while context.to_delete_pipelines_ids:
        pipeline_id = context.to_delete_pipelines_ids.pop(0)
        try:
            context.dl.pipelines.delete(pipeline_id=pipeline_id)
        except context.dl.exceptions.NotFound:
            pass
        except:
            all_deleted = False
            logging.exception('Failed deleting pipeline: ')
    assert all_deleted


@fixture
def delete_converter_dataset(context):
    if hasattr(context, 'platform_dataset'):
        context.platform_dataset.delete(True, True)


@fixture
def delete_services(context):
    if not hasattr(context, 'to_delete_services_ids'):
        return

    all_deleted = True
    while context.to_delete_services_ids:
        service_id = context.to_delete_services_ids.pop(0)
        try:
            context.dl.services.delete(service_id=service_id)
        except context.dl.exceptions.NotFound:
            pass
        except:
            all_deleted = False
            logging.exception('Failed deleting service: ')
    assert all_deleted
