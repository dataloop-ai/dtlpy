import dtlpy as dl
try:
    # for local import
    from tests.env_from_git_branch import get_env_from_git_branch
except ImportError:
    # for remote import
    from env_from_git_branch import get_env_from_git_branch

import sys


if __name__ == "__main__":
    args = sys.argv
    username = args[1]
    password = args[2]
    client_id = args[3]
    client_secret = args[4]
    env_name = None
    try:
        env_name = args[5]
        if env_name not in ['dev', 'rc', 'prod']:
            print('{} is unsupported env'.format(env_name))
            env_name = None
    except:
        pass

    if env_name is None:
        env_name = get_env_from_git_branch()
    dl.setenv(env_name)
    print('Environment is: {}'.format(env_name))

    dl.login_secret(
        email=username,
        password=password,
        client_id=client_id,
        client_secret=client_secret
    )

    if dl.token_expired():
        sys.exit(1)
    else:
        sys.exit(0)
