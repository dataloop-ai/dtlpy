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


def test_feature_file(w_feature_filename):
    log_path = os.path.join(TEST_DIR, 'logs')
    if not os.path.isdir(log_path):
        os.makedirs(log_path, exist_ok=True)
    print('Starting feature file: {}'.format(feature_filepath))
    log_filepath = None
    w_i_try = -1
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
            p.communicate()
            if p.returncode == 0:
                break

        if log_filepath is None:
            results[w_feature_filename] = {'status': False,
                                           'log_file': '',
                                           'try': w_i_try}
        else:
            directory, file = os.path.split(log_filepath)
            if p.returncode == 0:
                # passes
                new_log_filepath = os.path.join(directory, 'pass_' + file)
                if os.path.isfile(log_filepath):
                    os.rename(log_filepath, new_log_filepath)
                results[w_feature_filename] = {'status': True,
                                               'log_file': new_log_filepath,
                                               'try': w_i_try}
            else:
                # failed
                new_log_filepath = os.path.join(directory, 'fail_' + file)
                if os.path.isfile(log_filepath):
                    os.rename(log_filepath, new_log_filepath)
                results[w_feature_filename] = {'status': False,
                                               'log_file': new_log_filepath,
                                               'try': w_i_try}
    except:
        print(traceback.format_exc())
        results[w_feature_filename] = {'status': False,
                                       'log_file': log_filepath,
                                       'try': w_i_try}


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
    dl.setenv('dev')
    # check token
    payload = jwt.decode(dl.token(), algorithms=['HS256'], verify=False)
    if payload['email'] not in ['oa-test-1@dataloop.ai', 'oa-test-2@dataloop.ai', 'oa-test-3@dataloop.ai']:
        assert False, 'Cannot run test on user: "{}". only test users'.format(payload['email'])

    # run tests
    pool = ThreadPool(processes=32)
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
            print('{}\t in try: {}\tfeature: {}'.format(status, i_try, feature))

    # print passes
    for feature, result in results.items():
        if result['status']:
            status = 'passed' if result['status'] else 'failed'
            log_filename = result['log_file']
            i_try = result['try']
            print('{}\t in try: {}\tfeature: {}'.format(status, i_try, feature))

    # return success/failure
    if passed:
        # all True - passed
        sys.exit(0)
    else:
        sys.exit(1)
