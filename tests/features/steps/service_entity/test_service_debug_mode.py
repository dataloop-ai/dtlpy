import dtlpy as dl
import behave
import time
from operator import attrgetter


@behave.when(u'I update service mode to "{service_mode}"')
def step_impl(context, service_mode):
    context.service.mode = {'type': service_mode}
    context.service = context.service.update()


@behave.then(u'I validate service has "{instance_number}" instance up')
def step_impl(context, instance_number):
    """ Get service instances / pods / replicas status """
    num_try = 60
    interval = 10
    success = False

    for i in range(num_try):
        time.sleep(interval)
        status = context.service.status()
        context.service_instances = status['runtimeStatus']
        if len(context.service_instances) == int(instance_number):
            success = True
            break
        context.dl.logger.debug("Step is running for {:.2f}[s] and now Going to sleep {:.2f}[s]".format((i + 1) * interval,
                                                                                                        interval))

    assert success, "TEST FAILED: Expected {}, Got {}".format(instance_number, len(context.service_instances))


@behave.then(u'I validate path "{path}" get response "{expected_response}" interval: "{interval}" tries: "{num_try}"')
def step_impl(context, path, expected_response, interval=20, num_try=5):
    interval = int(interval)
    num_try = int(num_try)
    """ Get service instances / pods / replicas status """
    assert path.find("{") != -1 and path.find("}") != -1, "Please provide correct template. For example: dataset/{dataset.id}/query"
    if not path.startswith('/'):
        path = '/{}'.format(path)

    success = False

    resource = path[path.find("{") + 1:path.find("}")]
    #  Build the path to get resource id from context: {}#1 - prefix, {}#2 - resource.id, {}#3 - suffix
    path = "{}{}{}".format(path[:path.find("{")], attrgetter(resource)(context), path[path.find("}") + 1:])

    for i in range(num_try):
        success, response = dl.client_api.gen_request(req_type="get",
                                                      path=path)
        if success:
            break
        dl.logger.warning("Try number {}".format(i + 1))
        dl.logger.warning("Request failed with error message {}".format(response.text))
        time.sleep(interval)

    assert success, "TEST FAILED: Request failed. {}".format(response.text)
    assert expected_response in response.text, "TEST FAILED: Expected response to include {}. Actual got {}".format(expected_response, response.text)
