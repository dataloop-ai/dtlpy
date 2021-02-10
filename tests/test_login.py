import dtlpy as dl

try:
    # for local import
    from tests.env_from_git_branch import get_env_from_git_branch
except ImportError:
    # for remote import
    from env_from_git_branch import get_env_from_git_branch

import sys
import os


def test_login():
    env_name = get_env_from_git_branch()
    dl.setenv(env_name)
    if env_name in ['rc', 'dev']:
        username = os.environ["TEST_USERNAME"]
        password = os.environ["TEST_PASSWORD"]
        client_id = os.environ["TEST_CLIENT_ID"]
        client_secret = os.environ["TEST_CLIENT_SECRET"]
    elif env_name == 'prod':
        username = os.environ["TEST_USER_PROD"]
        password = os.environ["TEST_PASSWORD_PROD"]
        client_id = os.environ["CLIENT_ID_PROD"]
        client_secret = os.environ["CLIENT_SECRET_PROD"]
    else:
        raise ValueError('unknown env alias: {}'.format(env_name))
    dl.login_secret(
        email=username,
        password=password,
        client_id=client_id,
        client_secret=client_secret
    )

    if dl.token_expired():
        print('Token Expired')
        sys.exit(1)
    else:
        print('Success')
        sys.exit(0)


if __name__ == "__main__":
    test_login()
