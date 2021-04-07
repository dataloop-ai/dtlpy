from behave.__main__ import main as behave_main
import logging
logging.basicConfig(level='DEBUG')
feature_filename = 'test_snapshots_create.feature'

behave_main(['tests/features', '-i', feature_filename, '--stop', '--no-capture'])
