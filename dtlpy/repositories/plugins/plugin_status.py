from dtlpy.utilities.plugin_bootstraping.util import get_state_json
import dtlpy

def get_status_from_folder():
    try:
        state_json = get_state_json()
    except:
        raise Exception('.dataloop/state.json not found, you might have not run dlp plugins init')

    if not 'package' in state_json:
        raise Exception('Please run "dlp checkout plugin <plugin_name>" first')

    plugin_name = state_json['package']

    try:
        plugin = dtlpy.tasks.get(task_name=plugin_name)
    except:
        raise Exception('Plugin not found, you should run dlp plugins push first')

    print(dtlpy.plugins.status(plugin.id))