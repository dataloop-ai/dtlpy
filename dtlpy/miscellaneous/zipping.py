import pathspec
import logging
import zipfile
import os

logger = logging.getLogger(name=__name__)


class Zipping:
    def __init__(self):
        pass

    @staticmethod
    def zip_directory(zip_filename, directory=None):
        """
        Zip Directory
        Will ignore .gitignore files

        :param directory:
        :param zip_filename:
        :return:
        """
        # default path
        if directory is None:
            directory = os.getcwd()
        # check if directory
        assert os.path.isdir(directory), '[ERROR] Directory does not exists: %s' % directory

        if '.gitignore' in os.listdir(directory):
            with open(os.path.join(directory, '.gitignore')) as f:
                spec_src = f.read()
        else:
            spec_src = ''
        spec = pathspec.PathSpec.from_lines(pathspec.patterns.GitWildMatchPattern, spec_src.splitlines())

        # init zip file
        zip_file = zipfile.ZipFile(zip_filename, 'w', zipfile.ZIP_DEFLATED)

        for root, dirs, files in os.walk(directory):
            for file in files:
                filepath = os.path.join(root, file)
                if not spec.match_file(filepath):
                    zip_file.write(filepath, arcname=os.path.join('dist', os.path.relpath(filepath, directory)))

        # finally
        zip_file.close()

    @staticmethod
    def unzip_directory(zip_filename, to_directory=None):
        zip_ref = zipfile.ZipFile(zip_filename, 'r')
        # the zip contains the full directory so
        # unzipping straight to path (without another directory)
        if not to_directory:
            to_directory = '.'
        zip_ref.extractall(to_directory)
        zip_ref.close()
        return to_directory
