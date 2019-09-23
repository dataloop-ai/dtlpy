# Run this main to locally debug your plugin
import os


def debug():
    print('debug')
    print(os.getcwd())
    os.chdir('..')
    # run the plugin
    import dtlpy
    print(dtlpy.plugins.test_local_plugin())


if __name__ == '__main__':
    debug()
