import subprocess
import threading
import traceback
import json
import time
import jwt
import os
import dtlpy as dl
import numpy as np
from multiprocessing.pool import ThreadPool
from tqdm import tqdm
import sys


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
NUM_TRIES = 3


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
        i_project.delete(True, True)
    except Exception:
        try:
            for dataset in i_project.datasets.list():
                try:
                    if dataset.readonly:
                        dataset.set_readonly(False)
                except Exception:
                    pass
            for app in i_project.apps.list().items:
                try:
                    app.uninstall()
                except Exception:
                    pass
            for dpkg in i_project.dpks.list().items:
                try:
                    dpkg.delete()
                except Exception:
                    pass
            for service in i_project.services.list().items:
                try:
                    service.delete()
                except Exception:
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
    log_path = os.path.join(TEST_DIR, 'logs')
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
                    '-i', w_feature_filename,
                    '--stop',
                    '-o', log_filepath,
                    '--logging-level=DEBUG',
                    '--summary',
                    '--no-capture']
            # need to run a new process to avoid collisions
            p = subprocess.Popen(cmds, stderr=subprocess.PIPE)
            _, stderr = p.communicate(timeout=1000)

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

    except subprocess.TimeoutExpired:
        results[w_feature_filename] = {'status': True,
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
    pool = ThreadPool(processes=4)
    features_path = os.path.join(TEST_DIR, 'features')

    results = dict()
    features_to_run = set()
    for path, subdirs, files in os.walk(features_path):
        for filename in files:
            striped, ext = os.path.splitext(filename)
            if ext in ['.feature']:
                features_to_run.add(os.path.join(path, filename))

    pbar = tqdm(total=len(features_to_run), desc="Features progress")

    test_state = TestState()
    test_state.start()

    for feature_filename in features_to_run:
        results[feature_filename] = dict()
        time.sleep(.1)
        pool.apply_async(test_feature_file, kwds={'w_feature_filename': feature_filename, 'i_pbar': pbar})

    pool.close()
    pool.join()
    pbar.close()

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
    all_results = [result['status'] for result in results.values()]
    passed = all(all_results)

    if not passed:
        if sys.argv.__len__() > 1 and sys.argv[1] == 'scheduled':
            send_alert()
        print('-------------- Logs --------------')
        for feature, result in results.items():
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

    # print timeouts
    for feature, result in tests_results:
        if result.get('timeout', False):
            status = 'timeout'
            log_filename = result['log_file']
            i_try = result['try']
            avg_time = result['avgTime']
            res_msg = '{}\t in try: {}\tavg time: {}\tfeature: {} , timeout'.format(status, i_try, avg_time, os.path.basename(feature))
            print(res_msg)

    # print failed first
    for feature, result in tests_results:
        if not result['status']:
            status = 'failed'
            log_filename = result['log_file']
            i_try = result['try']
            avg_time = result['avgTime']
            res_msg = '{}\t in try: {}\tavg time: {}\tfeature: {}'.format(status, i_try, avg_time, os.path.basename(feature))
            print(res_msg)

    # print passes
    for feature, result in tests_results:
        if result['status']:
            status = 'passed'
            log_filename = result['log_file']
            i_try = result['try']
            avg_time = result['avgTime']
            res_msg = '{}\t in try: {}\tavg time: {}\tfeature: {}'.format(status, i_try, avg_time, os.path.basename(feature))
            print(res_msg)

    # return success/failure
    if passed:
        # all True - passed
        sys.exit(0)
    else:
        sys.exit(1)
