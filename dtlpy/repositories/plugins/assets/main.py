import dtlpy

def run(item):
    print("The item is: {}".format(item))
    assert isinstance(item, dtlpy.entities.Item)
    return item.to_json()

if __name__=="__main__":
    ##Run this main to locally debug your plugin

    #run the plugin
    dtlpy.plugins.test_local_plugin()