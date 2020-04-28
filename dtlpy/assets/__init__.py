import os
from .service_runners import service_runner_paths


class PATHS:
    PACKAGE_FILENAME = 'package.json'
    SERVICE_FILENAME = 'service.json'
    GITIGNORE_FILENAME = 'package_gitignore'
    MAIN_FILENAME = 'main.py'
    MOCK_FILENAME = 'mock.json'
    ADAPTER_MODEL = 'adapter_model.py'
    PARTIAL_MAIN = 'main_partial.py'
    MODULE_A_FILENAME = 'first_module_class.py'
    MODULE_B_FILENAME = 'second_module_class.py'

    ASSETS_PATH = os.path.dirname(__file__)
    ASSETS_MAIN_FILEPATH = os.path.join(ASSETS_PATH, MAIN_FILENAME)
    ASSETS_MOCK_FILEPATH = os.path.join(ASSETS_PATH, MOCK_FILENAME)
    ASSETS_PACKAGE_FILEPATH = os.path.join(ASSETS_PATH, PACKAGE_FILENAME)
    ASSETS_SERVICE_FILEPATH = os.path.join(ASSETS_PATH, SERVICE_FILENAME)
    ASSETS_GITIGNORE_FILEPATH = os.path.join(ASSETS_PATH, GITIGNORE_FILENAME)
    ASSETS_ADAPTER_MODEL_FILEPATH = os.path.join(ASSETS_PATH, ADAPTER_MODEL)
    PARTIAL_MAIN_FILEPATH = os.path.join(ASSETS_PATH, PARTIAL_MAIN)


paths = PATHS()
