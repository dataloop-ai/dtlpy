import os


class PATHS:
    PACKAGE_FILENAME = 'package.json'
    SERVICE_FILENAME = 'service.json'
    GITIGNORE_FILENAME = 'package_gitignore'
    MAIN_FILENAME = 'main.py'
    MOCK_FILENAME = 'mock.json'

    ASSETS_PATH = os.path.dirname(__file__)
    ASSETS_MAIN_FILEPATH = os.path.join(ASSETS_PATH, MAIN_FILENAME)
    ASSETS_MOCK_FILEPATH = os.path.join(ASSETS_PATH, MOCK_FILENAME)
    ASSETS_PACKAGE_FILEPATH = os.path.join(ASSETS_PATH, PACKAGE_FILENAME)
    ASSETS_SERVICE_FILEPATH = os.path.join(ASSETS_PATH, SERVICE_FILENAME)
    ASSETS_GITIGNORE_FILEPATH = os.path.join(ASSETS_PATH, GITIGNORE_FILENAME)


paths = PATHS()
