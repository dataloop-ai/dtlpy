import pathspec
import numpy as np
import logging
import zipfile
import os

logger = logging.getLogger(name=__name__)

MAX_ZIP_FILE = 100e6  # 100MB


class Zipping:
    def __init__(self):
        pass

    @staticmethod
    def zip_directory(zip_filename, directory=None, ignore_max_file_size=False):
        """
        Zip Directory
        Will ignore .gitignore files

        :param directory:
        :param zip_filename:
        :param ignore_max_file_size: ignore the limitation on the zip file size
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
        ignore_lines = spec_src.splitlines() + ['.git', '.dataloop']
        spec = pathspec.PathSpec.from_lines(pathspec.patterns.GitWildMatchPattern, ignore_lines)

        # init zip file
        zip_file = zipfile.ZipFile(zip_filename, 'w', zipfile.ZIP_DEFLATED)
        try:
            for root, dirs, files in os.walk(directory):
                for file in files:
                    filepath = os.path.join(root, file)
                    if not spec.match_file(filepath):
                        zip_file.write(filepath, arcname=os.path.relpath(filepath, directory))
                        if not ignore_max_file_size:
                            if np.sum([f.file_size for f in list(zip_file.NameToInfo.values())]) > MAX_ZIP_FILE:
                                logger.error('Failed zipping in file: {}'.format(filepath))
                                raise ValueError(
                                    'Zip file cant be over 100MB. '
                                    'Please verify that only code is being uploaded or '
                                    'add files to .gitignore so they wont be zipped and uploaded as code.')
        finally:
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
