import subprocess
import os


def get_env_from_git_branch():
    env_name = os.environ.get('DLP_ENV_NAME', None)
    if env_name is None:
        p = subprocess.Popen(['git', 'rev-parse', '--abbrev-ref', 'HEAD'],
                             stdout=subprocess.PIPE,
                             stderr=subprocess.PIPE)
        output, err = p.communicate()
        branch_name = str(output, 'utf-8').strip()
        if branch_name == 'rc':
            env_name = 'rc'
        elif branch_name == 'development':
            env_name = 'dev'
        elif branch_name == 'master':
            env_name = 'prod'
        else:
            env_name = 'dev'
            print('unknown git branch. default is "dev"')
    print('Running on dataloop environment: {!r}'.format(env_name))
    return env_name
