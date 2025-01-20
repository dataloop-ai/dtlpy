import time
import behave
import json
import os
import dtlpy as dl
from datetime import datetime, timedelta, timezone


@behave.given('I get plans resources json')
def step_impl(context):
    # fetch billing api calls
    path = os.path.join(os.environ['DATALOOP_TEST_ASSETS'], "billing", "billing_api_calls.json")
    with open(path, 'r') as file:
        billing_api_calls = json.load(file)

    # API request for the api_resources
    success, response = context.dl.client_api.gen_request(req_type="get", path=billing_api_calls['plans'])
    # Display the Error
    if not success:
        raise context.dl.exceptions.PlatformException(response)
    context.plans_resources = response.json()


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


@behave.given('I update quotas')
@behave.when('I update quotas')
def step_impl(context):
    # fetch billing api calls
    path = os.path.join(os.environ['DATALOOP_TEST_ASSETS'], "billing", "billing_api_calls.json")
    with open(path, 'r') as file:
        billing_api_calls = json.load(file)

    # _json = '{"org":"' + context.org.id + '"}'
    org_json = {"org": context.org.id}
    success, response = dl.client_api.gen_request(req_type='post',
                                                  path=billing_api_calls['aggregation'].replace('account_id',
                                                                                                context.org.account[
                                                                                                    "id"]),
                                                  json_req=org_json
                                                  )

    if not success:
        raise context.dl.exceptions.PlatformException(response)
    response_json = response.json()
    command = context.dl.Command.from_json(_json=response_json,
                                           client_api=dl.client_api)
    command.wait(timeout=0)


@behave.when('I get usage')
def step_impl(context):
    # fetch billing api calls
    path = os.path.join(os.environ['DATALOOP_TEST_ASSETS'], "billing", "billing_api_calls.json")
    with open(path, 'r') as file:
        billing_api_calls = json.load(file)

    # Get the current date
    current_date = datetime.now()
    # Set the startDate to the first day of the current month
    startDate = datetime(current_date.year, current_date.month, 1).strftime('%Y-%m-%d')

    # Calculate the endDate as the first day of the next month
    if current_date.month == 12:
        endDate = datetime(current_date.year + 1, 1, 1).strftime('%Y-%m-%d')
    else:
        endDate = datetime(current_date.year, current_date.month + 1, 1).strftime('%Y-%m-%d')

    success, response = dl.client_api.gen_request(req_type='get',
                                                  path=billing_api_calls['usage'].replace('account_id',
                                                                                          context.org.account["id"])
                                                       + f"?startDate={startDate}&endDate={endDate}"
                                                  )

    if not success:
        raise context.dl.exceptions.PlatformException(response)


@behave.then('I unable to upload items')
def step_impl(context):
    filepath = "0000000162.jpg"
    filepath = os.path.join(os.environ['DATALOOP_TEST_ASSETS'], filepath)

    filename = 'file'

    uploaded_filename = filename + 'me.jpg'
    import io
    with open(filepath, 'rb') as f:
        buffer = io.BytesIO(f.read())
        buffer.name = uploaded_filename
    try:
        context.dataset.items.upload(
            local_path=buffer,
            remote_path=None
        )
        context.error = None
    except Exception as e:
        context.error = e


@behave.when('I delete the free subscription')
def step_impl(context):
    # fetch billing api calls
    path = os.path.join(os.environ['DATALOOP_TEST_ASSETS'], "billing", "billing_api_calls.json")
    with open(path, 'r') as file:
        billing_api_calls = json.load(file)

    num_try = 60
    interval = 5
    for i in range(num_try):
        success, response = context.dl.client_api.gen_request(req_type="get",
                                                              path=billing_api_calls['get_free'].replace('org_id',
                                                                                                         context.org.id))

        if success:
            break
        time.sleep(interval)

    if not success:
        raise context.dl.exceptions.PlatformException(response)

    context.subscription = response.json()

    success, response = context.dl.client_api.gen_request(req_type="post",
                                                          path=billing_api_calls['cancel'].replace('subscription_id',
                                                                                                   context.subscription["id"]))

    if not success:
        raise context.dl.exceptions.PlatformException(response)


@behave.Then('I unable to activate service')
def step_impl(context):
    services = context.project.services.list().items
    service = dl.services.get(service_id=services[0].id)
    if not service.active:
        try:
            service.active = True
            service.update()
            context.error = None
            service = dl.services.get(service_id=services[0].id)
        except Exception as e:
            context.error = e
    else:
        assert False, f"TEST FAILED: service already active"


@behave.Then('I activate service')
def step_impl(context):
    services = context.project.services.list().items
    service = dl.services.get(service_id=services[0].id)
    if service.active:
        service.active = False
        service.update()
        service = dl.services.get(service_id=services[0].id)
        if not service.active:
            service.active = True
            service.update()
            service = dl.services.get(service_id=services[0].id)
            assert service.active, f"TEST FAILED: Unable to activate service"
        else:
            assert False, f"TEST FAILED: Unable to deactivate service"
    else:
        assert False, f"TEST FAILED: Service already inactive"


@behave.Then('I deactivate service named "{service_name}"')
def step_impl(context, service_name):
    services = context.project.services.list().items
    # Iterate through the services to find the one with the correct name
    for service in services:
        if service.name == service_name:
            service = dl.services.get(service_id=service.id)
            if service.active:
                service.active = False
                service.update()
                service = dl.services.get(service_id=service.id)
                assert not service.active, f"TEST FAILED: Unable to deactivate service '{service_name}'"
            else:
                assert False, f"TEST FAILED: Service '{service_name}' is already inactive"
            break
    else:
        assert False, f"TEST FAILED: Service with name '{service_name}' not found"


@behave.when(u'I update context.service')
def step_impl(context):
    num_try = 60
    interval = 7
    success = False

    for i in range(num_try):
        time.sleep(interval)
        services = context.project.services.list().items
        if services:
            service = dl.services.get(service_id=services[0].id)
            context.service = service
            success = True
            break
        context.dl.logger.debug(
            "Step is running for {:.2f}[s] and now Going to sleep {:.2f}[s]".format((i + 1) * interval,
                                                                                    interval))

    assert success, "TEST FAILED: Expected 1-service, Got {}".format(len(services))


@behave.when('I get analytics query "{pod_type}" for {sec} seconds')
def step_impl(context, pod_type, sec):


    # fetch billing api calls
    path = os.path.join(os.environ['DATALOOP_TEST_ASSETS'], "billing", "billing_api_calls.json")
    with open(path, 'r') as file:
        billing_api_calls = json.load(file)

    # fetch analytics query json
    path = os.path.join(os.environ['DATALOOP_TEST_ASSETS'], "billing", "analytics_query.json")
    with open(path, 'r') as file:
        analytics_query = json.load(file)

    # Get current UTC time and calculate previous and next day
    current_utc_datetime = datetime.now(timezone.utc)
    previous_day_datetime = current_utc_datetime - timedelta(days=1)
    next_day_datetime = current_utc_datetime + timedelta(days=1)

    # Convert to Unix timestamps
    previous_day_formatted = int(previous_day_datetime.timestamp() * 1000)
    next_day_formatted = int(next_day_datetime.timestamp() * 1000)

    # Edit JSON
    analytics_query["context"]["projectId"] = [context.project.id]  # Ensure projectId is an array
    analytics_query["startTime"] = previous_day_formatted
    analytics_query["endTime"] = next_day_formatted

    # Initialize or increment num_services
    if not hasattr(context, 'index_num') or context.index_num is None:
        # If 'num_services' doesn't exist in the context or is None, initialize it to 0 or 1
        context.index_num = 0  # or set to 1 if you prefer starting from 1
    else:
        # Increment 'num_services' by 1 on each run
        context.index_num += 1

    start_time = datetime.now()
    # Loop until the condition is met
    while True:

        # Check if 10 minutes have passed
        elapsed_time = (datetime.now() - start_time).total_seconds()
        if elapsed_time >= 600:  # 600 seconds = 10 minutes
            assert False, "Operation timed out after 10 minutes."

        # Make the API request to get updated data
        success, response = dl.client_api.gen_request(
            req_type='post',
            path=billing_api_calls['analytics_query'],
            json_req=analytics_query
        )

        if not success:
            raise context.dl.exceptions.PlatformException(response)
        num_seconds = 0
        response_json = response.json()

        # Check if the response contains any data
        if response_json[0].get('response', []):
            index_num = context.index_num  # Reset index_num each time a new request is made

            while index_num >= 0:
                # Check the response value for the current service
                try:
                    # Access the current response item safely
                    response_item = response_json[0].get('response', [])[index_num]
                    active_pod_type = response_item.get('podType', 0)

                    if pod_type == active_pod_type:
                        num_seconds = response_item.get('seconds', 0)
                        if num_seconds >= int(sec):
                            context.dl.logger.info(f"Condition met: num_seconds is {sec} or more.")
                            break  # Break out of the inner while loop
                        else:
                            context.dl.logger.info(f"num_seconds {num_seconds} is less than {sec}. Checking again after 30 seconds...")
                            time.sleep(30)  # Wait before checking again
                            break  # Break out of the inner while loop to make a new request
                    else:
                        context.dl.logger.info(f"Expected podType - {pod_type}, Actual podType - {active_pod_type}")
                        # Decrement index_num to check the next service
                        index_num -= 1

                except IndexError:
                    context.dl.logger.info("IndexError: No response for the current service number. Retrying...")
                    time.sleep(30)
                    index_num -= 1  # Decrement index_num and retry
                    continue

            # If the condition is met, break out of the outer loop
            if num_seconds >= int(sec):
                break  # Break out of the outer while loop

        else:
            context.dl.logger.info("No valid 'response' found in the JSON. Retrying after 30 seconds...")
            time.sleep(30)