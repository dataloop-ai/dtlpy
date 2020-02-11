from .. import entities

DEFAULT_PACKAGE_ENTRY_POINT = 'main.py'

DEFAULT_PACKAGE_FUNCTION_NAME = 'run'
DEFAULT_PACKAGE_MODULE_NAME = 'default_module'
DEFAULT_PACKAGE_NAME = 'default_package'

DEFAULT_PACKAGE_METHOD = entities.PackageFunction(name=DEFAULT_PACKAGE_FUNCTION_NAME,
                                                  description='',
                                                  inputs=[],
                                                  outputs=[])
DEFAULT_PACKAGE_MODULE = entities.PackageModule(init_inputs=list(),
                                                entry_point=DEFAULT_PACKAGE_ENTRY_POINT,
                                                name=DEFAULT_PACKAGE_MODULE_NAME,
                                                functions=[DEFAULT_PACKAGE_METHOD])
