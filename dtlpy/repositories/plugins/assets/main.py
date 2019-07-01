import dtlpy
import os
def run(item):
    print("The item is: {}".format(item))

if __name__=="__main__":
    ##Run this main to locally debug your plugin
    #Change to plugin root
    os.chdir("..")
    #run the plugin
    dtlpy.plugins.test_local_plugin()