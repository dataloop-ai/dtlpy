import behave
import time


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
