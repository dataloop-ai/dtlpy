from behave.__main__ import main as behave_main


# feature_filename = 'test_item_repo_methods.feature'
feature_filename = 'test_items_upload.feature'


behave_main(['tests/features', '-i', feature_filename, '--stop', '--no-capture'])
