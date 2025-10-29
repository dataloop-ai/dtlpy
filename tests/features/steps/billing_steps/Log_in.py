import behave
import dtlpy as dl
import os


@behave.given('I log in as a "{user_type}"')
@behave.when('I log in as a "{user_type}"')
def step_impl(context, user_type):
    if user_type == 'superuser':
        username = os.environ["TEST_SU_USERNAME"]
        password = os.environ["TEST_SU_PASSWORD"]
    elif user_type == 'user':
        username = os.environ["TEST_USERNAME"]
        password = os.environ["TEST_PASSWORD"]
    else:
        assert False, 'Wrong user_type the options are: "superuser", "user"'

    login = dl.login_m2m(
        email=username,
        password=password,
    )
    assert login, f"TEST FAILED: User login failed"
    if user_type == 'superuser':
        context.scenario.return_to_user = True
    elif  user_type == 'user':
        context.scenario.return_to_user = False
    context.dl = dl
