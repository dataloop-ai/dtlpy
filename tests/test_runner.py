import subprocess
import traceback
import json
import time
import sys
import os
import dtlpy as dl
import numpy as np
from multiprocessing.pool import ThreadPool

TEST_DIR = os.path.dirname(os.path.realpath(__file__))
NUM_TRIES = 2


def clean_feature_log_file(log_filepath):
    if os.path.isfile(log_filepath):
        os.remove(log_filepath)
    directory, file = os.path.split(log_filepath)
    if os.path.isfile(os.path.join(directory, 'pass_' + file)):
        os.remove(os.path.join(directory, 'pass_' + file))
    if os.path.isfile(os.path.join(directory, 'fail_' + file)):
        os.remove(os.path.join(directory, 'fail_' + file))


def test_feature_file(w_feature_filename):
    log_filepath = os.path.join(TEST_DIR, 'logs', os.path.basename(w_feature_filename) + '.log')
    print('Starting feature file: {}'.format(feature_filepath))

    try:
        clean_feature_log_file(log_filepath)
        if not os.path.isdir(os.path.dirname(log_filepath)):
            os.makedirs(os.path.dirname(log_filepath), exist_ok=True)

        cmds = ['behave', features_path,
                '-i', w_feature_filename,
                '--stop',
                '-o', log_filepath,
                '--summary',
                '--no-capture']
        for i in range(NUM_TRIES):
            # need to run a new process to avoid collisions
            p = subprocess.Popen(cmds)
            p.communicate()
            if p.returncode == 0:
                break

        directory, file = os.path.split(log_filepath)
        if p.returncode == 0:
            # passes
            new_log_filepath = os.path.join(directory, 'pass_' + file)
            os.rename(log_filepath, new_log_filepath)
            results[w_feature_filename] = (True, new_log_filepath)
        else:
            # failed
            new_log_filepath = os.path.join(directory, 'fail_' + file)
            os.rename(log_filepath, new_log_filepath)
            results[w_feature_filename] = (False, new_log_filepath)
    except:
        print(traceback.format_exc())
        results[w_feature_filename] = (False, log_filepath)


if __name__ == '__main__':
    print('Running test from directory: {}'.format(TEST_DIR))

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
    dl.setenv('dev')

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
                results[filename] = (False, '')
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
    all_results = [result[0] for result in results.values()]
    passed = all(all_results)
    print('-------------- Summary --------------')
    print('Current loop api calls: ', str(api_calls))
    print('Tests took: ' + str(int((end_time - start_time) / 100)) + ' minutes')
    if passed:
        print('All scenarios passed!:')
    else:
        print('Failed {}/{}:'.format(np.sum([1 for res in all_results if res is False]), len(all_results)))
        for feature, result in results.items():
            status, log_filename = result
            if status is False:
                print('\t{}'.format(feature))
        print('Logs:')
        for feature, result in results.items():
            status, log_filename = result
            if status is False:
                with open(log_filename, 'r') as output:
                    print(output.read())

    # return success/failure
    if passed:
        # all True - passed
        sys.exit(0)
    else:
        sys.exit(1)
