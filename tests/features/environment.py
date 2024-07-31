import time

from behave import fixture, use_fixture
import os
import json
import logging
from filelock import FileLock
from dotenv import load_dotenv
import subprocess

from behave.reporter.summary import SummaryReporter
from behave.formatter.base import StreamOpener
import sys

import dtlpy as dl

try:
    # for local import
    from tests.env_from_git_branch import get_env_from_git_branch
except ImportError:
    # for remote import
    from ..env_from_git_branch import get_env_from_git_branch


def before_all(context):
    load_dotenv('.test.env')
    # Get index driver from env var
    context.index_driver_var = os.environ.get("INDEX_DRIVER_VAR", None)


@fixture
def after_feature(context, feature):
    print_feature_filename(context, feature)

    if hasattr(feature, 'bot'):
        try:
            feature.bot.delete()
        except Exception:
            logging.exception('Failed to delete bot')

    if hasattr(feature, 'apps'):
        for app in context.feature.apps:
            try:
                app.uninstall()
            except Exception:
                logging.exception('Failed to uninstall app')

    if hasattr(feature, 'dpks'):
        for dpk in context.feature.dpks:
            try:
                dpk.delete()
            except Exception:
                try:
                    apps = dl.apps.list(
                        filters=dl.Filters(use_defaults=False, resource=dl.FiltersResource.APP,
                                           field="dpkName",
                                           values=dpk.name))
                    for page in apps:
                        for app in page:
                            app.uninstall()
                    models = dl.models.list(
                        filters=dl.Filters(use_defaults=False, resource=dl.FiltersResource.MODEL,
                                           field="app.dpkName",
                                           values=dpk.name))
                    for page in models:
                        for model in page:
                            model.delete()
                    dpk.delete()
                except:
                    logging.exception('Failed to delete dpk')

    if hasattr(feature, 'dataloop_feature_integration'):
        all_deleted = True
        time.sleep(7)  # Wait for drivers to delete
        for integration_id in feature.to_delete_integrations_ids:
            try:
                feature.dataloop_feature_project.integrations.delete(integrations_id=integration_id, sure=True,
                                                                     really=True)
            except feature.dataloop_feature_dl.exceptions.NotFound:
                pass
            except:
                all_deleted = False
                logging.exception('Failed deleting integration: {}'.format(integration_id))
        assert all_deleted

    if hasattr(feature, 'dataloop_feature_project'):
        try:
            if 'frozen_dataset' in feature.tags:
                fix_project_with_frozen_datasets(project=feature.dataloop_feature_project)
            feature.dataloop_feature_project.delete(True, True)
        except Exception:
            logging.exception('Failed to delete project')

    if hasattr(context.feature, 'dataloop_feature_org'):
        try:
            username = os.environ["TEST_SU_USERNAME"]
            password = os.environ["TEST_SU_PASSWORD"]
            login = dl.login_m2m(
                email=username,
                password=password
            )
            assert login, "TEST FAILED: User login failed"
            context.dl = dl
            success, response = dl.client_api.gen_request(req_type='delete',
                                                          path=f'/orgs/{feature.dataloop_feature_org.id}')
            if not success:
                raise dl.exceptions.PlatformException(response)
            logging.info(f'Organization id {feature.dataloop_feature_org.id} deleted successfully')
            username = os.environ["TEST_USERNAME"]
            password = os.environ["TEST_PASSWORD"]
            login = dl.login_m2m(
                email=username,
                password=password
            )
            assert login, "TEST FAILED: User login failed"
            context.dl = dl
            return True
        except Exception:
            logging.exception('Failed to delete organization')

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


@fixture
def before_scenario(context, scenario):
    context.scenario.return_to_user = False


@fixture
def after_scenario(context, scenario):
    if context.scenario.return_to_user == True:
        username = os.environ["TEST_USERNAME"]
        password = os.environ["TEST_PASSWORD"]
        login = dl.login_m2m(
            email=username,
            password=password,
        )
        assert login, "TEST FAILED: User login failed"
        print("----------Changed to a Regular user----------")
        context.scenario.return_to_user = False
        context.dl = dl


def get_step_key(step):
    return '{}: line {}. {}'.format(step.location.filename, step.location.line, step.name)


@fixture
def before_step(context, step):
    key = get_step_key(step)
    setattr(context, key, time.time())


@fixture
def after_step(context, step):
    key = get_step_key(step)
    start_time = getattr(context, key, None)
    total_time = time.time() - start_time
    if total_time > 3:
        print("######## {}\nStep Duration: {}".format(key, total_time))
    delattr(context, key)


@fixture
def before_feature(context, feature):
    if 'rc_only' in context.tags and 'rc' not in os.environ.get("DLP_ENV_NAME"):
        feature.skip("Marked with @rc_only")
        return
    if 'skip_test' in context.tags:
        feature.skip("Marked with @skip_test")
        return


def fix_project_with_frozen_datasets(project):
    datasets = project.datasets.list()
    for dataset in datasets:
        if dataset.readonly:
            dataset.set_readonly(False)


@fixture
def before_tag(context, tag):
    if "skip_test" in tag:
        """
        For example: @skip_test_DAT-99999
        """
        dat = tag.split("_")[-1] if "DAT" in tag else ""
        if hasattr(context, "scenario"):
            context.scenario.skip(f"Test mark as SKIPPED, Should be merged after {dat}")


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
    elif tag == 'datasets.delete':
        try:
            use_fixture(datasets_delete, context)
        except Exception:
            logging.exception('Failed to delete dataset')
    elif tag == 'drivers.delete':
        try:
            use_fixture(drivers_delete, context)
        except Exception:
            logging.exception('Failed to delete driver')
    elif tag == 'models.delete':
        try:
            use_fixture(models_delete, context)
        except Exception:
            logging.exception('Failed to delete model')
    elif tag == 'setenv.reset':
        try:
            use_fixture(reset_setenv, context)
        except Exception:
            logging.exception('Failed to reset env')
    elif tag == 'frozen_dataset':
        pass
    elif 'testrail-C' in tag:
        pass
    elif tag == 'wip':
        pass
    elif any(i_tag in tag for i_tag in ['DAT-', 'qa-', 'rc_only', 'skip_test']):
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
            filters = context.dl.Filters(resource=context.dl.FiltersResource.EXECUTION, field='latestStatus.status', values=['created', 'in-progress'], operator='in')
            filters.add(field='pipeline.id', values=pipeline_id)
            executions = context.dl.executions.list(filters=filters)
            for execution in executions.items:
                execution.terminate()
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


@fixture
def drivers_delete(context):
    if not hasattr(context, 'to_delete_drivers_ids'):
        return

    all_deleted = True
    time.sleep(25)  # Wait for datasets to delete
    for driver_id in context.to_delete_drivers_ids:
        try:
            context.project.drivers.delete(driver_id=driver_id, sure=True, really=True)
        except context.dl.exceptions.NotFound:
            pass
        except:
            all_deleted = False
            logging.exception('Failed deleting driver: {}'.format(driver_id))
    assert all_deleted


@fixture
def datasets_delete(context):
    if not hasattr(context, 'to_delete_datasets_ids'):
        return

    all_deleted = True
    for dataset_id in context.to_delete_datasets_ids:
        try:
            context.project.datasets.delete(dataset_id=dataset_id, sure=True, really=True)
        except context.dl.exceptions.NotFound:
            pass
        except:
            all_deleted = False
            logging.exception('Failed deleting dataset: {}'.format(dataset_id))
    assert all_deleted


@fixture
def reset_setenv(context):
    _, base_env = get_env_from_git_branch()
    cmds = ["dlp", "api", "setenv", "-e", "{}".format(base_env)]
    p = subprocess.Popen(cmds, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    context.out, context.err = p.communicate()
    # save return code
    context.return_code = p.returncode
    assert context.return_code == 0, "AFTER TEST FAILED: {}".format(context.err)


def print_feature_filename(context, feature):
    s_r = SummaryReporter(context.config)
    stream = getattr(sys, s_r.output_stream_name, sys.stderr)
    p_stream = StreamOpener.ensure_stream_with_encoder(stream)
    p_stream.write(f"Feature Finished : {feature.filename.split('/')[-1]}\n")
    p_stream.write(f"Status: {str(feature.status).split('.')[-1]} - Duration: {feature.duration:.2f} seconds\n")


@fixture
def models_delete(context):
    all_deleted = True
    if hasattr(context, 'to_delete_model_ids'):
        for model_id in context.to_delete_model_ids:
            try:
                context.project.models.delete(model_id=model_id)
            except context.dl.exceptions.NotFound:
                pass
            except:
                all_deleted = False
                logging.exception('Failed deleting model: {}'.format(model_id))

    for model in context.project.models.list().all():
        try:
            model.delete()
        except context.dl.exceptions.NotFound:
            pass
        except:
            all_deleted = False
            logging.exception('Failed deleting model: {}'.format(model.id))
    assert all_deleted