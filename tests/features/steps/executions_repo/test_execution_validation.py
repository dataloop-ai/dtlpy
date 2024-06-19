import behave
import time


@behave.then(u'I expect execution status progress include "{value}" in "{key}" with a frequency of "{frequency}"')
def step_impl(context, value, key, frequency):
    num_try = 30
    interval = 8
    success = False

    for i in range(num_try):
        time.sleep(interval)
        counter = 0
        execution = context.service.executions.get(execution_id=context.execution.id)
        statuses = execution.status
        for status in statuses:
            if eval(value) == status.get(key, None):
                counter += 1
                if counter == int(frequency):
                    success = True
                    break
    assert success, f"TEST FAILED: after {round(num_try * interval / 60, 1)} minutes"
