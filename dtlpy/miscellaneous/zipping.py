from typing import List

import pathspec
import numpy as np
import logging
import zipfile
import os

logger = logging.getLogger(name='dtlpy')

MAX_ZIP_FILE = 100e6  # 100MB


class Zipping:
    def __init__(self):
        pass

    @staticmethod
    def zip_directory(zip_filename, directory=None, ignore_max_file_size=False, ignore_directories: List[str] = None):
        """
        Zip Directory
        Will ignore .gitignore files

        :param directory:
        :param zip_filename:
        :param ignore_max_file_size: ignore the limitation on the zip file size
        :param list[str] ignore_directories: directories to ignore.
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
        if ignore_directories is not None:
            ignore_lines += ignore_directories
        spec = pathspec.PathSpec.from_lines(pathspec.patterns.GitWildMatchPattern, ignore_lines)

        # init zip file
        zip_file = zipfile.ZipFile(zip_filename, 'w', zipfile.ZIP_DEFLATED)
        try:
            for root, dirs, files in os.walk(directory):
                for file in files:
                    filepath = os.path.join(root, file)
                    if not spec.match_file(os.path.relpath(filepath, directory)):
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
        zipdata = zipfile.ZipFile(zip_filename)
        zipinfos = zipdata.infolist()

        # iterate through each file
        for zipinfo in zipinfos:
            # encode the file names
            # zip package make decode by cp437 for file that have name that not ascii
            # this happen when the flag_bits be different than 0
            # so we encode the name back
            if not zipinfo.flag_bits:
                zipinfo.filename = zipinfo.filename.encode('cp437').decode('utf-8')
            zipdata.extract(zipinfo, to_directory)
