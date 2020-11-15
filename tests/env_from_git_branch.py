import subprocess


def get_env_from_git_branch():
    env_name = 'dev'
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
        print('unknown git branch. default is "dev"')
    return env_name
