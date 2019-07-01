import os
from dtlpy.utilities.plugin_bootstraping.util import get_state_json
import dtlpy

class PackageUploader:
    def __init__(self):
        state_json = get_state_json()
        self.project_id = state_json['project']
        self.task_name = state_json['package']

    def upload_package(self):
        cwd = os.getcwd()
        dataloop_path = os.path.join(cwd, '.dataloop')

        if not os.path.exists(dataloop_path):
            print('No .dataloop folder found, please run "dlp init"')
            exit(-1)

        src_path = os.path.join(cwd, 'src')

        project = dtlpy.projects.get(project_id=self.project_id)
        package = project.packages.pack(directory=src_path, name=self.task_name)
        return package