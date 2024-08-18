import subprocess
import threading
import traceback
import json
import time
from concurrent.futures import ThreadPoolExecutor, wait

import jwt
import os
import dtlpy as dl
import numpy as np
from multiprocessing.pool import ThreadPool
from tqdm import tqdm
import sys
from filelock import FileLock
import random
import string

TIMEOUT = 1.8 * 60 * 60


class TestState(threading.Thread):
    def __init__(self):
        super(TestState, self).__init__()
        self._stop_event = threading.Event()
        self.state = dict()
        self.lock = threading.Lock()

    def run(self):
        while not self._stop_event.is_set():
            self.lock.acquire()
            state = self.state.copy()
            self.lock.release()
            message = 'Currently running tests:\n'
            try:
                for test in state.values():
                    message += '{} - {:.2f} seconds\n'.format(test['name'], time.time() - test['start'])
                print(message)
            except Exception:
                print('Failed to print state\n{}'.format(traceback.format_exc()))
            time.sleep(30)

    def start_test(self, test_name: str):
        self.lock.acquire()
        self.state[test_name] = {
            'start': time.time(),
            'name': test_name,
        }
        self.lock.release()

    def end_test(self, test_name: str):
        self.lock.acquire()
        self.state.pop(test_name, None)
        self.lock.release()

    def stop(self):
        self._stop_event.set()


try:
    # for local import
    from tests.env_from_git_branch import get_env_from_git_branch
except ImportError:
    # for remote import
    from env_from_git_branch import get_env_from_git_branch

TEST_DIR = os.path.dirname(os.path.realpath(__file__))
REPORT_DIR = os.path.join(TEST_DIR, 'reports')
NUM_TRIES = 2


def clean_feature_log_file(log_filepath):
    if os.path.isfile(log_filepath):
        os.remove(log_filepath)
    directory, file = os.path.split(log_filepath)
    if os.path.isfile(os.path.join(directory, 'pass_' + file)):
        os.remove(os.path.join(directory, 'pass_' + file))
    if os.path.isfile(os.path.join(directory, 'fail_' + file)):
        os.remove(os.path.join(directory, 'fail_' + file))


def delete_single_project(i_project: dl.Project, i_pbar):
    try:
        for dataset in i_project.datasets.list():
            try:
                if dataset.readonly:
                    dataset.set_readonly(False)
            except Exception:
                pass
        for pipeline in i_project.pipelines.list().items:
            try:
                pipeline.delete()
            except Exception:
                pass
        for service in i_project.services.list().items:
            try:
                service.delete()
            except Exception as e:
                if 'Service cannot be deleted as long as it has running/pending pipeline' in str(e):
                    services = service.executions.list()
                    for page in services:
                        for s in page:
                            try:
                                s.terminate()
                            except Exception as e:
                                pass
                pass
        for model in i_project.models.list().items:
            try:
                model.delete()
            except Exception:
                pass
        for app in i_project.apps.list().items:
            try:
                app.uninstall()
            except Exception:
                pass
        for dpkg in i_project.dpks.list(filters=dl.Filters(field='creator', values=dl.info()['user_email'],
                                                           resource=dl.FiltersResource.DPK)).items:
            try:
                dpkg.delete()
            except Exception:
                apps = dl.apps.list(
                    filters=dl.Filters(use_defaults=False, resource=dl.FiltersResource.APP,
                                       field="dpkName",
                                       values=dpkg.name))
                for page in apps:
                    for app in page:
                        try:
                            app.uninstall()
                        except Exception as e:
                            pass
                try:
                    dpkg.delete()
                except:
                    pass
        i_project.delete(True, True)
    except Exception:
        print('Failed to delete project: {}'.format(i_project.name))
    i_pbar.update(1)


def delete_projects():
    start_phrase = 'to-delete-test-'
    projects = [
        p for p in dl.projects.list() if p.creator.startswith('oa-test-') and p.name.startswith(start_phrase)
    ]

    projects_pbar = tqdm(total=len(projects), desc='Deleting projects')

    projects_pool = ThreadPool(processes=32)
    for p in projects:
        projects_pool.apply_async(delete_single_project, args=(p, projects_pbar))

    projects_pool.close()
    projects_pool.join()


def test_feature_file(w_feature_filename, i_pbar):
    timeout = 10 * 60
    longer_timeout = 16 * 60

    longer_timeout_features = [
        'pipeline_active_learning.feature',
        'test_service_debug_runtime.feature',
        'test_models_clone_1.feature',
        'pipeline_rerun_cycles_2.feature',
        'test_models_context.feature',
        'test_models_flow.feature',
        'execution_monitoring_terminate.feature',
        'execution_monitoring_timeout.feature',
        'pipeline_context.feature',
    ]

    log_path = os.path.join(TEST_DIR, 'logs')
    temp_report_filepath = os.path.join(REPORT_DIR, f'temp_report_{generate_random_string(8)}.json')
    if not os.path.isdir(log_path):
        os.makedirs(log_path, exist_ok=True)
    log_filepath = None
    w_i_try = -1
    tic = time.time()
    stderr = ''
    try:
        test_state.start_test(w_feature_filename)
        for w_i_try in range(NUM_TRIES):
            print('Attempt {} for feature file: {}'.format(w_i_try + 1, w_feature_filename))
            log_filepath = os.path.join(log_path,
                                        os.path.basename(w_feature_filename) + '_try_{}.log'.format(w_i_try + 1))
            clean_feature_log_file(log_filepath)
            cmds = ['behave', features_path,
                    '-i', w_feature_filename.split("/")[-1],
                    '--stop',
                    '-o', log_filepath,
                    '--format=pretty',
                    '--logging-level=DEBUG',
                    '--summary',
                    '--no-capture',
                    '--format=json',
                    '-o', temp_report_filepath,
                    '--format=pretty',
                    ]
            # need to run a new process to avoid collisions
            p = subprocess.Popen(cmds, stderr=subprocess.PIPE)
            _, stderr = p.communicate(
                timeout=longer_timeout if os.path.basename(w_feature_filename) in longer_timeout_features else timeout
            )

            if p.returncode == 0:
                break
        toc = time.time() - tic
        if log_filepath is None:
            results[w_feature_filename] = {'status': False,
                                           'log_file': '',
                                           'try': w_i_try,
                                           'avgTime': '{:.2f}[s]'.format(toc / (1 + w_i_try))}
        else:
            directory, file = os.path.split(log_filepath)
            if p.returncode == 0:
                # passes
                new_log_filepath = os.path.join(directory, 'pass_' + file)
                if os.path.isfile(log_filepath):
                    os.rename(log_filepath, new_log_filepath)
                results[w_feature_filename] = {'status': True,
                                               'log_file': new_log_filepath,
                                               'try': w_i_try,
                                               'avgTime': '{:.2f}[s]'.format(toc / (1 + w_i_try))}
            else:
                # failed
                new_log_filepath = os.path.join(directory, 'fail_' + file)
                if os.path.isfile(log_filepath):
                    os.rename(log_filepath, new_log_filepath)
                results[w_feature_filename] = {'status': False,
                                               'log_file': new_log_filepath,
                                               'try': w_i_try,
                                               'avgTime': '{:.2f}[s]'.format(toc / (1 + w_i_try))}
                print('**** Failed feature file: {} after {} seconds and {} retries.'.format(
                    w_feature_filename, toc, w_i_try + 1
                ))
                print('**** stderr: {}'.format(stderr))

            with open(temp_report_filepath, 'r') as json_file:
                try:
                    data = json.load(json_file)
                except json.JSONDecodeError:
                    print("The JSON file is empty or not a valid JSON.")
                    data = []
            # Need to check the feature folder
            feature_folder = w_feature_filename.split('/')[-2]
            feature_report_path = os.path.join(REPORT_DIR,
                                               f'{check_feature_folder(feature_folder).lower()}-report.json')
            with FileLock(feature_report_path + ".lock"):
                if os.path.exists(feature_report_path):
                    with open(feature_report_path, 'r+') as file:
                        file_content = file.read()
                        if file_content:
                            temp = json.loads(file_content)
                            if isinstance(temp, list):
                                if len(data) > 0:
                                    temp.append(data[0])
                                    # Move the cursor to the beginning of the file
                                    file.seek(0)
                                    # Write the updated list back to the file
                                    file.write(json.dumps(temp, indent=4))
                                    # Truncate the file to the current size to remove any leftover content
                                    file.truncate()
                            else:
                                raise Exception("Expected list in the report file")
                        else:
                            file.write(json.dumps(data, indent=4))

                else:
                    with open(feature_report_path, 'w') as file:
                        file.write(json.dumps(data, indent=4))


    except subprocess.TimeoutExpired:
        results[w_feature_filename] = {'status': False,
                                       'log_file': log_filepath,
                                       'try': w_i_try,
                                       'avgTime': '{:.2f}[s]'.format(-1),
                                       'timeout': True}
    except Exception:
        print(traceback.format_exc())
        results[w_feature_filename] = {'status': False,
                                       'log_file': log_filepath,
                                       'try': w_i_try,
                                       'avgTime': '{:.2f}[s]'.format(-1)}
    i_pbar.update(1)
    test_state.end_test(w_feature_filename)


def check_feature_folder(feature_folder):
    if feature_folder in ["assignments_repo", "tasks_repo"]:
        return "Ramsay"
    elif feature_folder in ["pipeline_entity", "pipeline_resume", "packages_entity", "packages_flow", "packages_repo",
                            "services_entity", "services_repo", "execution_monitoring", "executions_repo",
                            "triggers_repo"]:
        return "Piper"
    elif feature_folder in ["bot_entity", "bots_repo", "integrations_repo", "project_entity", "projects_repo"]:
        return "Hodor"
    elif feature_folder in ["app_entity", "dpk_tests", "solution", "app_integrations"]:
        return "Apps"
    elif feature_folder in ["command_entity", "dataset_entity", "datasets_repo", "drivers_repo", "ontologies_repo",
                            "ontology_entity", "recipe_entity", "recipes_repo", "artifacts_repo", "filters_entity",
                            "item_entity", "items_repo", "ann_text_object", "annotation_collection", "annotation_entity"
        , "annotations_repo", "features_vector_entity"]:
        return "Rubiks"
    elif feature_folder in ["checkout_testing", "cli_testing", "code_base_entity", "code_bases_repo", "converter",
                            "documentation_tests", "platform_urls", "webm_converter", "cache", "xray"]:
        return "SDK"
    elif feature_folder in ["settings"]:
        return "Woz"
    elif feature_folder in ["models_repo"]:
        return "Roberto"
    elif feature_folder in ["notifications"]:
        return "Hedwig"
    elif feature_folder in ["billing_repo"]:
        return "Billing"
    else:
        assert False, f"Feature folder '{feature_folder}' not in the services list - Please add it to correct condition"


def generate_random_string(length):
    """Generate a random string of numbers and letters."""
    # Define the character set: numbers and letters (uppercase and lowercase)
    characters = string.ascii_letters + string.digits
    # Generate a random string from the character set
    random_string = ''.join(random.choice(characters) for _ in range(length))
    return random_string


def create_project_for_alerts(contributors, project_name):
    project = dl.projects.create(project_name=project_name)
    for con in contributors:
        try:
            project.add_member(email=con, role='developer')
        except Exception:
            pass
    return project


def send_alert():
    recipients = [
        'aharon@dataloop.ai',
        'or@dataloop.ai'
    ]

    project_name = 'DataloopAlerts'

    try:
        project = dl.projects.get(project_name=project_name)
    except Exception:
        project = create_project_for_alerts(contributors=recipients, project_name=project_name)

    title = 'FAILED - PRODUCTION - SDK TESTS'
    msg = 'SDK tests in production failed'

    for rec in recipients:
        try:
            dl.projects._send_mail(project_id=project.id, send_to=rec, title=title, content=msg)
        except Exception:
            print('Failed to send mail to: {}'.format(rec))


def report_to_xray(test_env: str = 'RC'):
    services_list = ['Ramsay', 'Piper', 'Hodor', 'Apps', 'Rubiks', 'SDK', 'Woz', 'Roberto', 'Hedwig', 'Billing']

    """
    Check if all services has a report folder and remove from the list if not
    """
    test_env = test_env.upper()
    services_to_remove = []
    for service in services_list:
        if not os.path.exists(os.path.join(REPORT_DIR, f'{service.lower()}-report.json')):
            print(f"### !!! Missing report for service: {service} !!! ###")
            services_to_remove.append(service)

    for service in services_to_remove:
        services_list.remove(service)
    """
    Loop on all services and try to report to Xray using shell script
    """

    shell_script_path = os.path.join(os.getcwd(), 'xrayreporter.sh')
    subprocess.run(['chmod', '+x', shell_script_path])
    for service in services_list:
        print(f"### Reporting for service: {service} ###")
        report_path = os.path.join(REPORT_DIR, f'{service.lower()}-report.json')
        try:
            # Make the shell script executable (optional, do this only if it's not already executable)
            result = subprocess.run([shell_script_path, test_env, service, report_path], capture_output=True, text=True)
            print(result.stdout)
        except subprocess.CalledProcessError as e:
            print(f"### Failed to report for service: {service} ###")
            print(f"### Error: {e} ###")


if __name__ == '__main__':
    print('########################################')
    print('# Running test from directory: {}'.format(TEST_DIR))
    print('########################################')

    # reset SDK api calls
    dl.client_api.calls_counter.reset()
    dl.client_api.calls_counter.on()

    # zero out api call file
    call_counters_path = os.path.join(TEST_DIR, 'assets', 'api_calls.json')
    with open(call_counters_path, 'r') as f:
        api_calls = json.load(f)

    for api_call in api_calls:
        api_calls[api_call] = 0

    with open(call_counters_path, 'w') as f:
        api_calls = json.dump(api_calls, f, indent=2)

    # set timer and environment
    start_time = time.time()
    # set env to dev
    _, base_env = get_env_from_git_branch()
    dl.setenv(base_env)
    print('Environment is: {}'.format(base_env))

    print('########################################')
    print('# Deleting projects')
    print('########################################')
    delete_projects()

    # set log level
    dl.verbose.logging_level = "warning"
    dl.verbose.print_all_responses = True

    # check token
    payload = jwt.decode(dl.token(), algorithms=['HS256'], verify=False,
                         options={'verify_signature': False})
    if payload['email'] not in ['oa-test-1@dataloop.ai',
                                'oa-test-4@dataloop.ai',
                                'oa-test-2@dataloop.ai',
                                'oa-test-3@dataloop.ai']:
        assert False, 'Cannot run test on user: "{}". only test users'.format(payload['email'])

    # run tests
    pool = ThreadPoolExecutor(max_workers=6)
    features_path = os.path.join(TEST_DIR, 'features')
    if not os.path.exists(REPORT_DIR):
        os.makedirs(REPORT_DIR)
        assert os.path.exists(REPORT_DIR), f'Failed to create reports directory: {REPORT_DIR}'
        print(f"Created reports directory: {REPORT_DIR}")

    print(f"Index driver is {os.environ.get('INDEX_DRIVER_VAR', None)}")

    results = dict()
    features_to_run = set()
    for path, subdirs, files in os.walk(features_path):
        if "billing_repo" not in path:
            for filename in files:
                striped, ext = os.path.splitext(filename)
                if ext in ['.feature']:
                    features_to_run.add(os.path.join(path, filename))

    pbar = tqdm(total=len(features_to_run), desc="Features progress")

    test_state = TestState()
    test_state.start()

    _futures = []
    for feature_filename in features_to_run:
        results[feature_filename] = dict()
        time.sleep(.1)
        future = pool.submit(test_feature_file, **{'w_feature_filename': feature_filename, 'i_pbar': pbar})
        _futures.append(future)

    # Wait for all futures to complete or timeout
    done, not_done = wait(_futures, timeout=TIMEOUT)

    if not_done:
        print("Timeout reached. Not all tasks completed within 2 hours.")
        for future in not_done:
            future.cancel()

    pbar.close()
    pool.shutdown(wait=False)

    test_state.stop()

    # stop timer
    end_time = time.time()

    # get call count
    call_counters_path = os.path.join(TEST_DIR, 'assets', 'api_calls.json')
    with open(call_counters_path, 'r') as f:
        api_calls = json.load(f)

    # print results
    api_calls = sum(api_calls.values())

    # Summary
    all_results = [result.get('status', False) for result in results.values()]
    passed = all(all_results)

    if not passed:
        if sys.argv.__len__() > 1 and sys.argv[1] == 'scheduled':
            send_alert()
        print('-------------- Logs --------------')
        for feature, result in results.items():
            if not result:
                continue
            status = result['status']
            log_filename = result['log_file']
            i_try = result['try']
            if status is False:
                try:
                    with open(log_filename, 'r') as output:
                        print(output.read())
                except:
                    continue
    print('-------------- Summary --------------')
    print('Current loop api calls: ', str(api_calls))
    print('Tests took: {:.2f}[s]'.format(end_time - start_time))
    if passed:
        print(
            'All scenarios passed! {}/{}:'.format(np.sum([1 for res in all_results if res is True]), len(all_results)))
    else:
        print('Failed {}/{}:'.format(np.sum([1 for res in all_results if res is False]), len(all_results)))

    tests_results = results.items()

    # print timeout first
    for feature, result in tests_results:
        if result and not result.get('status', None) and 'timeout' in result:
            status = 'timeout'
            log_filename = result['log_file']
            i_try = result['try']
            avg_time = result['avgTime']
            res_msg = '{}\t in try: {}\tavg time: {}\tfeature: {}'.format(status, i_try, avg_time,
                                                                          os.path.basename(feature))
            print(res_msg)

    # print failed first
    for feature, result in tests_results:
        if result and not result.get('status', None) and 'timeout' not in result:
            status = 'failed'
            log_filename = result['log_file']
            i_try = result['try']
            avg_time = result['avgTime']
            res_msg = '{}\t in try: {}\tavg time: {}\tfeature: {}'.format(status, i_try, avg_time,
                                                                          os.path.basename(feature))
            print(res_msg)

    # print unrun tests
    for feature, result in tests_results:
        if not result:
            status = 'unrun'
            res_msg = '{}\t in try: {}\tavg time: {}\tfeature: {}'.format(status, 0, 0, os.path.basename(feature))
            print(res_msg)

    # print passes
    for feature, result in tests_results:
        if result and result.get('status'):
            status = 'passed'
            log_filename = result['log_file']
            i_try = result['try']
            avg_time = result['avgTime']
            res_msg = '{}\t in try: {}\tavg time: {}\tfeature: {}'.format(status, i_try, avg_time,
                                                                          os.path.basename(feature))
            print(res_msg)

    delete_projects()

    report_to_xray(test_env=base_env)

    # return success/failure
    if passed:
        # all True - passed
        sys.exit(0)
    else:
        sys.exit(1)
