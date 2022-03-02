import subprocess
import traceback
import json
import time
import jwt
import sys
import os
import dtlpy as dl
import numpy as np
from multiprocessing.pool import ThreadPool

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


def delete_projects():
    start_phrase = 'to-delete-test-'

    try:
        projects = [p for p in dl.projects.list() if p.name.startswith(start_phrase) and (
                p.creator.startswith('oa-test-1') or p.creator.startswith('oa-test-2') or
                p.creator.startswith('oa-test-3') or p.creator.startswith('oa-test-4'))]
        for p in projects:
            p.delete(True, True)
    except Exception:
        print('Failed to delete projects')


def test_feature_file(w_feature_filename):
    log_path = os.path.join(TEST_DIR, 'logs')
    if not os.path.isdir(log_path):
        os.makedirs(log_path, exist_ok=True)
    print('Starting feature file: {}'.format(feature_filepath))
    log_filepath = None
    w_i_try = -1
    tic = time.time()
    try:
        for w_i_try in range(NUM_TRIES):
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
            p = subprocess.Popen(cmds)
            p.communicate(timeout=700)

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


import sys


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
    env_name = get_env_from_git_branch()
    dl.setenv(env_name)
    print('Environment is: {}'.format(env_name))

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
    # go over all file and run ".feature" files
    for path, subdirs, files in os.walk(features_path):
        for filename in files:
            striped, ext = os.path.splitext(filename)
            if ext in ['.feature']:
                feature_filepath = os.path.join(path, filename)
                results[filename] = dict()
                time.sleep(1)
                pool.apply_async(test_feature_file, kwds={'w_feature_filename': filename})

    pool.close()
    pool.join()
    pool.terminate()

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

    # print failed first
    for feature, result in results.items():
        if not result['status']:
            status = 'passed' if result['status'] else 'failed'
            log_filename = result['log_file']
            i_try = result['try']
            avg_time = result['avgTime']
            res_msg = '{}\t in try: {}\tavg time: {}\tfeature: {}'.format(status, i_try, avg_time, feature)
            if 'timeout' in result:
                res_msg += '  timeout'
            print(res_msg)

    # print passes
    for feature, result in results.items():
        if result['status']:
            status = 'passed' if result['status'] else 'failed'
            log_filename = result['log_file']
            i_try = result['try']
            avg_time = result['avgTime']
            res_msg = '{}\t in try: {}\tavg time: {}\tfeature: {}'.format(status, i_try, avg_time, feature)
            if 'timeout' in result:
                res_msg += '  timeout'
            print(res_msg)

    # delete projects
    delete_projects()

    # return success/failure
    if passed:
        # all True - passed
        sys.exit(0)
    else:
        sys.exit(1)
