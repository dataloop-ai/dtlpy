import dtlpy as dl

try:
    # for local import
    from tests.env_from_git_branch import get_env_from_git_branch
except ImportError:
    # for remote import
    from env_from_git_branch import get_env_from_git_branch

import sys
import os


def update_env_cookie_file(env_name, base_env):
    if base_env in ['prod', 'rc', 'dev']:
        return

    if base_env not in [env_dict['alias'] for env_url, env_dict in dl.client_api.environments.items()]:
        dl.add_environment(
            environment='https://{}-gate.dataloop.ai/api/v1'.format(base_env),
            verify_ssl=True,
            alias='{}'.format(base_env),
            gate_url="https://{}-gate.dataloop.ai".format(base_env),
            url="https://{}.dataloop.ai/".format(env_name)
        )

    assert base_env in [env_dict['alias'] for env_url, env_dict in dl.client_api.environments.items()], "Failed to add_environment: {}".format(env_name)

def test_login():
    env_name, base_env = get_env_from_git_branch()
    # Check if needed to add new env to cookie file
    update_env_cookie_file(env_name, base_env)
    dl.setenv(base_env)
    if env_name == 'prod':
        username = os.environ["TEST_USER_PROD"]
        password = os.environ["TEST_PASSWORD_PROD"]
    else:
        username = os.environ["TEST_USERNAME"]
        password = os.environ["TEST_PASSWORD"]

    dl.login_m2m(
        email=username,
        password=password,
    )

    if dl.token_expired():
        print('Token Expired')
        sys.exit(1)
    else:
        print('Success')
        sys.exit(0)


if __name__ == "__main__":
    test_login()
