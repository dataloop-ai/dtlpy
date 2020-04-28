import os


class PATHS:
    MULTI_METHOD = 'multi_method.py'
    MULTI_METHOD_JSON = 'multi_method_json.py'
    MULTI_METHOD_ITEM = 'multi_method_item.py'
    SINGLE_METHOD_DATASET = 'single_method_dataset.py'
    SINGLE_METHOD = 'single_method.py'
    SINGLE_METHOD_MULTI_INPUT = 'single_method_multi_input.py'
    MULTI_METHOD_DATASET = 'multi_method_dataset.py'
    SINGLE_METHOD_JSON = 'single_method_json.py'
    SINGLE_METHOD_ITEM = 'single_method_item.py'
    SINGLE_METHOD_ANNOTATION = 'single_method_annotation.py'
    MULTI_METHOD_ANNOTATION = 'multi_method_annotation.py'

    ASSETS_PATH = os.path.dirname(__file__)
    MULTI_METHOD_SR_PATH = os.path.join(ASSETS_PATH, MULTI_METHOD)
    MULTI_METHOD_JSON_SR_PATH = os.path.join(ASSETS_PATH, MULTI_METHOD_JSON)
    MULTI_METHOD_ITEM_SR_PATH = os.path.join(ASSETS_PATH, MULTI_METHOD_ITEM)
    SINGLE_METHOD_DATASET_SR_PATH = os.path.join(ASSETS_PATH, SINGLE_METHOD_DATASET)
    SINGLE_METHOD_SR_PATH = os.path.join(ASSETS_PATH, SINGLE_METHOD)
    MULTI_METHOD_DATASET_SR_PATH = os.path.join(ASSETS_PATH, MULTI_METHOD_DATASET)
    SINGLE_METHOD_JSON_SR_PATH = os.path.join(ASSETS_PATH, SINGLE_METHOD_JSON)
    SINGLE_METHOD_ITEM_SR_PATH = os.path.join(ASSETS_PATH, SINGLE_METHOD_ITEM)
    SINGLE_METHOD_ANNOTATION_SR_PATH = os.path.join(ASSETS_PATH, SINGLE_METHOD_ANNOTATION)
    MULTI_METHOD_ANNOTATION_SR_PATH = os.path.join(ASSETS_PATH, MULTI_METHOD_ANNOTATION)
    SINGLE_METHOD_MULTI_INPUT_SR_PATH = os.path.join(ASSETS_PATH, SINGLE_METHOD_MULTI_INPUT)


service_runner_paths = PATHS()
