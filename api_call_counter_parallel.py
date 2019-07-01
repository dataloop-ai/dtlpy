import json
import subprocess
import os
import dtlpy as dl
from multiprocessing.pool import ThreadPool
import time
import sys

results = dict()
dl.client_api.calls_counter.reset()
dl.client_api.calls_counter.on()


def test_feature_file(test_path):
    log_filename = os.path.join(os.getcwd(), 'tests', 'logs', os.path.basename(test_path) + '.log')
    if os.path.isfile(log_filename):
        os.remove(log_filename)
    if not os.path.isdir(os.path.dirname(log_filename)):
        os.makedirs(os.path.dirname(log_filename), exist_ok=True)
    # cmds = ['behave', test_path]
    cmds = ['behave', test_path, '-o', log_filename]
    for i in range(2):
        p = subprocess.Popen(cmds)
        p.communicate()
        if p.returncode == 0:
            break
    if p.returncode == 1:
        with open(log_filename, 'r') as output:
            print(output.read())
    results[test_path] = p.returncode


if __name__ == '__main__':
    
    # # clean api_call json
    # api_call_path = os.path.join(os.getcwd(), 'tests', 'assets', 'api_calls.json')
    # with open(api_call_path, 'r') as f:
    #     api_calls = json.load(f)
    # for feature in api_calls:
    #     api_calls[feature] = 0
    # with open(api_call_path, 'w') as f:
    #     json.dump(api_calls, f)

    start_time = time.time()
    dl.setenv('dev')
    pool = ThreadPool(processes=32)
    features_path = os.path.join(os.getcwd(), 'tests', 'features')
    for directory in os.listdir(features_path):
        if directory != 'steps' and not directory.startswith('.'):
            repo_path = os.path.join(features_path, directory)
            for feature_file in os.listdir(repo_path):
                feature_file_path = os.path.join(repo_path, feature_file)
                results[feature_file_path] = False
                time.sleep(.4)
                pool.apply_async(test_feature_file, kwds={'test_path': feature_file_path})

    pool.close()
    pool.join()
    pool.terminate()

    end_time = time.time()

    call_counters_path = os.path.join(os.getcwd(), 'tests', 'assets', 'api_calls.json')
    with open(call_counters_path, 'r') as f:
        api_calls = json.load(f)

    api_calls = sum(api_calls.values())
    print('Current loop api calls: ', str(api_calls))
    print('Tests took: ' + str(int((end_time-start_time)/100)) + ' minutes')

    if any(results.values()):
        sys.exit(1)
    else:
        sys.exit(0)

