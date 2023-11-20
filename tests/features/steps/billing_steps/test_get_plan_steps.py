import behave
import dtlpy as dl
import time
import os


@behave.then('Validate plan "{field}" is "{value}"')
def step_impl(context, field, value):
    num_try = 20
    interval = 10
    finished = False
    for i in range(num_try):
        success, response = context.dl.client_api.gen_request(req_type="get",
                                                              path=os.path.join(context.json_object["plg"]["start"],
                                                                                context.org.id,
                                                                                context.json_object["plg"]["end"]))
        if success == True:
            finished = True
            break
        time.sleep(interval)
    assert finished, f"TEST FAILED: Expected PLG plan and fail after {round(num_try * interval / 60, 1)} minutes"
    sub = eval(response.text.replace("true", "True"))
    plan = {"Type": sub['plan']['name'],
            # plan_answer = "Free" / "Basic / "Standard" / "Pro" / "Pro Plus"
            "Period": sub['period']
            # plan_answer = "monthly" / "annually"
            }
    assert plan[field] == value, f"TEST FAILED: Expected {value} got {plan[field]}"
