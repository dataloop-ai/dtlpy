import behave
import dtlpy as dl
import sys
import time
import datetime
import json
import os


@behave.given('I create "{entity}" name "{name}"')
@behave.when('I create "{entity}" name "{name}"')
def step_impl(context, entity, name):
    """
    :param context:
    :param entity: org / project / dataset
    :param name: object name
    :return:
    """

    context.num = time.time()
    context.name = f'to-delete-test-{name}_{int(context.num)}'

    if entity == "org":
        success, response = dl.client_api.gen_request(req_type='post',
                                                      path='/orgs',
                                                      json_req={"name": context.name}
                                                      )

        context.org = dl.entities.Organization.from_json(client_api=dl.client_api,
                                                         _json=response.json())

        assert isinstance(context.org, context.dl.entities.Organization)

        context.feature.dataloop_feature_org = context.org
        if not success:
            raise context.dl.exceptions.PlatformException(response)

    elif entity == "project":

        context.project = dl.projects.create(project_name=context.name)

        assert isinstance(context.project, context.dl.entities.Project)

        context.feature.dataloop_feature_project = context.project

    elif entity == "dataset":

        context.dataset = context.project.datasets.create(dataset_name=context.name)

    else:
        sys.exit("You must specify object as either 'org' 'project' 'dataset'")


@behave.given('I create custom subscription')
@behave.when('I create custom subscription')
def step_impl(context):

    # fetch billing api calls
    path = os.path.join(os.environ['DATALOOP_TEST_ASSETS'], "billing", "billing_api_calls.json")
    with open(path, 'r') as file:
        billing_api_calls = json.load(file)

    current_utc_datetime = datetime.datetime.now(datetime.UTC)
    next_year_datetime = current_utc_datetime.replace(year=current_utc_datetime.year + 1)
    utc_formated = current_utc_datetime.strftime('%Y-%m-%dT00:00:00.000Z')
    next_year_formated = next_year_datetime.strftime('%Y-%m-%dT00:00:00.000Z')
    context.json_object['startDate'] = utc_formated
    context.json_object['endDate'] = next_year_formated
    context.json_object['scope']['entityId'] = context.org.id

    params = context.table.headings
    for param in params:
        param = param.split("=")
        if param[0] == "annotation-tool-hours":
            context.json_object['plan']['resources'][0]['amount'] = float(param[1])
        if param[0] == "data-points":
            context.json_object['plan']['resources'][1]['amount'] = int(param[1])
        if param[0] == "api-calls":
            context.json_object['plan']['resources'][2]['amount'] = int(param[1])
        if param[0] == "hosted-storage":
            context.json_object['plan']['resources'][3]['amount'] = float(param[1])
        if param[0] == "system-compute":
            context.json_object['plan']['resources'][4]['amount'] = float(param[1])
        if param[0] == "compute-cpu-regular-xs":
            context.json_object['plan']['resources'][5]['amount'] = float(param[1])
        if param[0] == "compute-cpu-regular-s":
            context.json_object['plan']['resources'][6]['amount'] = float(param[1])
        if param[0] == "compute-cpu-regular-m":
            context.json_object['plan']['resources'][7]['amount'] = float(param[1])
        if param[0] == "compute-cpu-regular-l":
            context.json_object['plan']['resources'][8]['amount'] = float(param[1])
        if param[0] == "compute-cpu-highmem-xs":
            context.json_object['plan']['resources'][9]['amount'] = float(param[1])
        if param[0] == "compute-cpu-highmem-s":
            context.json_object['plan']['resources'][10]['amount'] = float(param[1])
        if param[0] == "compute-cpu-highmem-m":
            context.json_object['plan']['resources'][11]['amount'] = float(param[1])
        if param[0] == "compute-cpu-highmem-l":
            context.json_object['plan']['resources'][12]['amount'] = float(param[1])
        if param[0] == "compute-gpu-k80-s":
            context.json_object['plan']['resources'][13]['amount'] = float(param[1])
        if param[0] == "compute-gpu-k80-m":
            context.json_object['plan']['resources'][14]['amount'] = float(param[1])
        if param[0] == "compute-gpu-t4":
            context.json_object['plan']['resources'][15]['amount'] = float(param[1])
        if param[0] == "compute-gpu-t4-m":
            context.json_object['plan']['resources'][16]['amount'] = float(param[1])
        if param[0] == "compute-gpu-a100-s":
            context.json_object['plan']['resources'][17]['amount'] = float(param[1])
        if param[0] == "compute-gpu-a100-m":
            context.json_object['plan']['resources'][18]['amount'] = float(param[1])
        if param[0] == "account":
            context.json_object['account'] = context.org.account['id']

    success, response = dl.client_api.gen_request(req_type='post',
                                                  path=billing_api_calls['create_custom'],
                                                  json_req=context.json_object
                                                  )

    if not success:
        raise context.dl.exceptions.PlatformException(response)


@behave.given('I "{action}" enable-custom-subscription-blocking = True')
@behave.when('I "{action}" enable-custom-subscription-blocking = True')
def step_impl(context, action):

    # fetch billing api calls
    path = os.path.join(os.environ['DATALOOP_TEST_ASSETS'], "billing", "billing_api_calls.json")
    with open(path, 'r') as file:
        billing_api_calls = json.load(file)

    if action == "create":
        context.json_object['scope']['id'] = context.org.id
        success, response = dl.client_api.gen_request(req_type='post',
                                                      path=billing_api_calls['ff'],
                                                      json_req=context.json_object
                                                      )
        context.ff_response = response.json()
        if not success:
            raise context.dl.exceptions.PlatformException(response)

    elif action == "delete":
        context.json_object['scope']['id'] = context.org.id
        success, response = dl.client_api.gen_request(req_type='delete',
                                                      path=billing_api_calls['ff'] + context.ff_response['id'],
                                                      )
        if not success:
            raise context.dl.exceptions.PlatformException(response)
