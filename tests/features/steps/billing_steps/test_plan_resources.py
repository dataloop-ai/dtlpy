import behave
import json
import os
import dtlpy as dl


@behave.given('I get plans resources json')
def step_impl(context):
    # API request for the api_resources
    success, response = context.dl.client_api.gen_request(req_type="get", path="/plans")
    # Display the Error
    if not success:
        raise context.dl.exceptions.PlatformException(response)
    context.plans_resources = json.loads(response.text)


@behave.then('I validate "{plan_type}" plan resources')
def step_impl(context, plan_type):
    plans_types = {"Free": 0,
                   "Basic": 1,
                   "Standard": 2,
                   "Pro": 3,
                   "Pro Plus": 4
                   }
    api_resources = context.plans_resources[plans_types[plan_type]]

    if plan_type == "Free":
        json_resources = context.json_object["Free"]
    if plan_type == "Basic":
        json_resources = context.json_object["Basic"]
    if plan_type == "Standard":
        json_resources = context.json_object["Standard"]
    if plan_type == "Pro":
        json_resources = context.json_object["Pro"]
    if plan_type == "Pro Plus":
        json_resources = context.json_object["Pro Plus"]

    assert json_resources == api_resources, f"TEST FAILED: Expected {json_resources} got {api_resources}"


@behave.when('I fetch "{file_name}" file from "{folder_name}"')
@behave.given('I fetch "{file_name}" file from "{folder_name}"')
def step_impl(context, folder_name, file_name):
    path = os.path.join(os.environ['DATALOOP_TEST_ASSETS'], folder_name, file_name)
    with open(path, 'r') as file:
        context.json_object = json.load(file)
