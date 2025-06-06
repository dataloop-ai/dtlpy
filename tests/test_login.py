import dtlpy as dl

try:
    # for local import
    from tests.env_from_git_branch import get_env_from_git_branch
except ImportError:
    # for remote import
    from env_from_git_branch import get_env_from_git_branch

import sys
import os
from datetime import datetime


def update_env_cookie_file(env_name, base_env):
    if base_env in ['prod', 'rc', 'dev', 'custom']:
        return

    if base_env not in [env_dict['alias'] for env_url, env_dict in dl.client_api.environments.items()]:
        dl.add_environment(
            environment=os.environ.get("ENVIRONMENT_SDK", f'https://{base_env}-gate.dataloop.ai/api/v1'),
            verify_ssl=eval(os.environ.get("VERIFY_SSL_SDK", "True")),
            alias=f'{base_env}',
            gate_url=os.environ.get("GATE_URL_SDK", f"https://{base_env}-gate.dataloop.ai"),
            url=os.environ.get("URL_SDK", f"https://{base_env}.dataloop.ai")
        )

    assert base_env in [env_dict['alias'] for env_url, env_dict in
                        dl.client_api.environments.items()], "Failed to add_environment: {}".format(env_name)


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


def test_login_api_key():
    env_name, base_env = get_env_from_git_branch()
    # Check if needed to add new env to cookie file
    update_env_cookie_file(env_name, base_env)
    dl.setenv(base_env)
    dl.client_api.generate_api_key(description=f'Key generated by SDK automation {datetime.now()}', login=True)
    print('Success with API key')


if __name__ == "__main__":
    test_login()
    # If you want to test login with API key, set API_KEY to 'true'
    if os.environ.get("API_KEY", None) == 'true':
        # Update the login token to use API key
        test_login_api_key()
    sys.exit(0)


