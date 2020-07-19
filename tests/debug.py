from behave.__main__ import main as behave_main
import logging
logging.basicConfig(level='DEBUG')
feature_filename = 'test_items_upload_dataframe.feature'
# feature_filename = 'test_triggers_delete.feature'

behave_main(['tests/features', '-i', feature_filename, '--stop', '--no-capture'])
