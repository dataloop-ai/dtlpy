import os
from .service_runners import service_runner_paths


class PATHS:
    PACKAGE_FILENAME = 'package.json'
    GITIGNORE_FILENAME = 'package_gitignore'
    MAIN_FILENAME = 'main.py'
    MOCK_FILENAME = 'mock.json'
    MODEL_ADAPTER = 'model_adapter.py'
    PARTIAL_MAIN = 'main_partial.py'
    MODULE_A_FILENAME = 'first_module_class.py'
    MODULE_B_FILENAME = 'second_module_class.py'
    REQUIREMENTS_FILENAME = 'requirements.txt'

    ASSETS_PATH = os.path.dirname(__file__)
    ASSETS_MAIN_FILEPATH = os.path.join(ASSETS_PATH, MAIN_FILENAME)
    ASSETS_MOCK_FILEPATH = os.path.join(ASSETS_PATH, MOCK_FILENAME)
    ASSETS_PACKAGE_FILEPATH = os.path.join(ASSETS_PATH, PACKAGE_FILENAME)
    ASSETS_GITIGNORE_FILEPATH = os.path.join(ASSETS_PATH, GITIGNORE_FILENAME)
    ASSETS_MODEL_ADAPTER_FILEPATH = os.path.join(ASSETS_PATH, MODEL_ADAPTER)
    PARTIAL_MAIN_FILEPATH = os.path.join(ASSETS_PATH, PARTIAL_MAIN)


paths = PATHS()
