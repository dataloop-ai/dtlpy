import behave
import time


@behave.then(u'I validate service has "{instance_number}" instance up')
@behave.then(u'I validate service has "{instance_number}" instance up and replicaId include service name "{flag}"')
@behave.then(u'I validate service has "{instance_number}" instance up and replicaId include service name "{flag}" num_try {num_try_input:d}')
def step_impl(context, instance_number, flag="None", num_try_input=60):
    """ Get service instances / pods / replicas status """
    num_try = num_try_input
    interval = 10
    success = False

    for i in range(num_try):
        time.sleep(interval)
        status = context.service.status()
        context.service_instances = status['runtimeStatus']
        if len(context.service_instances) == int(instance_number):
            success = True
            if eval(flag):
                for instance in context.service_instances:
                    assert context.service.name in instance['replicaId'], "TEST FAILED: Expected {} in {}, Got {}".format(
                        context.service.name, instance['replicaId'], instance)
            break
        context.dl.logger.debug(f"Step is running for {(i + 1) * interval:.2f}[s]. Sleeping for {interval:.2f}[s]")

    assert success, "TEST FAILED: Expected {}, Got {}".format(instance_number, len(context.service_instances))
