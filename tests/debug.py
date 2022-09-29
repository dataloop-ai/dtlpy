from behave.__main__ import main as behave_main
import logging
import os
logging.basicConfig(level='DEBUG')
feature_filename = 'test_models_create.feature'

os.environ['AVOID_TESTRAIL'] = 'true'
behave_main(['tests/features', '-i', feature_filename, '--stop', '--no-capture'])
