from dtlpy.utilities.checkout_manager.state_manager import get_state, set_state

def checkout_plugin(plugin_name):
    state_json = get_state()
    state_json['package'] = plugin_name
    set_state(state_json)
    print("Checkout out to plugin {}".format(plugin_name))