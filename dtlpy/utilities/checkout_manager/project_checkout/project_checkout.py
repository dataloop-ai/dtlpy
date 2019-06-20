import os
import json
from dtlpy.utilities.state_manager import get_state, set_state

def load_json_from_file(filepath):
    file_as_str = open(filepath, 'r').read()
    return json.loads(file_as_str)

def save_json_to_file(filepath, target_json):
    file = open(filepath, 'w+')
    file.write(json.dumps(target_json))

def get_project_by_identifier(projects, identifier):
    projects_by_name = [proj for proj in projects if proj.name == identifier]
    if (len(projects_by_name) == 1):
        return projects_by_name[0]
    elif (len(projects_by_name) > 1):
        print('Multiple projects with this name exist')
        exit(-1)

    projects_by_partial_id = [proj for proj in projects if proj.id.startswith(identifier)]
    if (len(projects_by_partial_id) == 1):
        return projects_by_partial_id[0]
    elif (len(projects_by_partial_id) > 1):
        print("Multiple projects whose id begins with {} exist".format(identifier))
        exit(-1)

    print("Project not found")
    exit(-1)

def checkout_project(dlp, project_identifier):
    state_json = get_state()

    projects = dlp.projects.list()
    project = get_project_by_identifier(projects, project_identifier)

    if ('project' in state_json and state_json['project'] == project.id):
        print('Already checked out to this project')
        exit(0)

    state_json['project'] = project.id
    if ('dataset' in state_json):
        del state_json['dataset']

    set_state(state_json)

    print('Checked out to project {}'.format(project.name))