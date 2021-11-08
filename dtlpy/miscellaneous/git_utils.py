import subprocess
import logging
import os

logger = logging.getLogger(name=__name__)


class GitUtils:
    """
    Performs git related methods
    """

    @staticmethod
    def git_included(path):
        """
        Get only included git repo files based on .gitignore file

        :param path: directory - str
        :return: list()
        """
        included_files = list()

        try:
            p = subprocess.Popen(['git', '--git-dir', os.path.join(path, '.git'), 'ls-files'],
                                 stdout=subprocess.PIPE,
                                 stderr=subprocess.PIPE)
            output, err = p.communicate()
            string_output = str(output, 'utf-8')
            included_files = string_output.split('\n')
        except Exception:
            logging.warning('Error getting git info for git repository in: {}'.format(path))
            # include all files
            for r, d, f in os.walk(path):
                for folder in d:
                    included_files.append(os.path.join(r, folder))

        return included_files

    @staticmethod
    def is_git_repo(path):
        """
        Check if directory is a git repo

        :param path: directory - str
        :return: True/False
        """
        try:
            p = subprocess.Popen(['git', '--git-dir', os.path.join(path, '.git'), '--work-tree', path, 'status'],
                                 stdout=subprocess.PIPE,
                                 stderr=subprocess.PIPE)
            output, err = p.communicate()
            if p.returncode != 0 and 'not a git repository' in str(err):
                response = False
            elif p.returncode == 0 and 'On branch' in str(output):
                response = True
            else:
                response = False
        except Exception:
            response = False
            logging.warning('Error getting git info for git repository in: {}'.format(path))
        return response

    @staticmethod
    def git_status(path):
        """
        Get git repository git status

        :param path: directory - str
        :return: String
        """
        status = dict()
        try:
            p = subprocess.Popen(['git', '--git-dir', os.path.join(path, '.git'), '--work-tree', path, 'status'],
                                 stdout=subprocess.PIPE,
                                 stderr=subprocess.PIPE)
            output, err = p.communicate()
            output_lines = str(output, 'utf-8').splitlines()
            branch = output_lines[0].replace('On branch ', '').strip()

            logs = GitUtils.git_log(path)
            status = {'branch': branch,
                      'commit_id': logs[0]['commit'],
                      'commit_author': logs[0]['Author'],
                      'commit_message': logs[0]['message']}
        except Exception:
            logging.warning('Error getting git info for git repository in: {}'.format(path))

        return status

    @staticmethod
    def git_url(path):
        """
        Get git remote url

        :param path: directory - str
        :return: String
        """
        url = ''
        try:
            p = subprocess.Popen(
                ['git', '--git-dir', os.path.join(path, '.git'), 'config', '--get', 'remote.origin.url'],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE)
            output, err = p.communicate()
            url = str(output, 'utf-8').splitlines()[0]

        except Exception:
            logging.warning('Error getting git info for git repository in: {}'.format(path))

        return url

    @staticmethod
    def git_log(path):
        """
        Get git repository git log

        :param path: directory - str
        :return: log as list()
        """
        log = list()
        try:
            log_limit = 100
            p = subprocess.Popen(['git', '--git-dir', os.path.join(path, '.git'), '--work-tree', path, 'log'],
                                 stdout=subprocess.PIPE,
                                 stderr=subprocess.PIPE)
            output, err = p.communicate()
            string_output = str(output, 'utf-8').split('\ncommit')
            for output in string_output:
                output = output.split('\n')
                if output[0].startswith('commit'):
                    output[0] = output[0].replace('commit', '')
                log_line = {
                    'commit': output[0].strip(),
                    'Author': output[1].replace('Author:', '').strip(),
                    'Date': output[2].replace('Date:', '').strip(),
                    'message': output[4].strip(),
                }
                log.append(log_line)
            log = log[0:log_limit]
        except Exception:
            logging.warning('Error getting git log for git repository in: {}'.format(path))

        return log

    @staticmethod
    def git_clone(path, git_url, **kwargs):
        """
        Clone git repo to local path
        :param path: `str` local path to clone to
        :param git_url: `str` git url to clone from
        :return `bool` for successful clone
        """
        if not os.path.isdir(path):
            os.makedirs(path)
        try:
            tag = kwargs.get('tag')
            branch = kwargs.get('branch')
            if tag is not None:
                branch_cmd = ['--branch', tag]
            elif branch is not None:
                branch_cmd = ['--branch', branch]
            else:
                branch_cmd = []

            cmd = ['git', 'clone'] + branch_cmd + [git_url, path]
            p = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            output, err = [std.decode() for std in p.communicate()]
            exit_code = p.returncode
            response = not exit_code
            if exit_code:
                logging.error('Error executing:  {ps1} $ {cmd}\n{err}'.format(ps1=path, cmd=' '.join(cmd), err=err))
        except Exception:
            response = False
            logging.warning('Error cloning git to: {}'.format(path))
        return response

    @staticmethod
    def git_command(path, cmd, show=False):
        """
        Execute command for a local git repo in path
        :param path: `str` local path for the git repo
        :param cmd:  `str` or `list` of `str` specifying the command to run
        :param show: `bool` if True, prints the stdout of the process (default=False)
        :return:  `bool` if command was successful or not
        """
        prev_dir = os.getcwd()
        if isinstance(cmd, str):
            cmd = cmd.split()

        try:
            os.chdir(path)
            p = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            output, err = p.communicate()
            output, err = output.decode(), err.decode()
            exit_code = p.returncode
            response = not exit_code
            # Print the process stdout / stderr
            if show:
                print(output)
            if exit_code:
                logging.error('Error executing:  {ps1} $ {cmd}\n{err}'.format(ps1=path, cmd=' '.join(cmd), err=err))
        except Exception:
            response = False
            logging.critical('Error executing:  {ps1} $ {cmd}'.format(ps1=path, cmd=' '.join(cmd)))
        finally:
            os.chdir(prev_dir)
        return response
