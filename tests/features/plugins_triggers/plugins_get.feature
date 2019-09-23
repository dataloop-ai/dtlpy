Feature: Plugins repository push function testing

    Background: Initiate Platform Interface and create a project
        Given Platform Interface is initialized as dlp and Environment is set to development
        And There is a project by the name of "test_plugins_get"
        And Directory "plugins_get" is empty
        When I generate plugin by the name of "test_plugin" to "plugins_get"

    @plugins.delete
    Scenario: Get plugin by name
        When I push "first" plugin
            |package_id=None|plugin_name=test_plugin|src_path=plugins_get|inputs=None|outputs=None|
        When I get plugin by the name of "test_plugin"
        Then I get a plugin entity
        And It is equal to plugin created

    @plugins.delete
    Scenario: Get plugin by id
        When I push "first" plugin
            |package_id=None|plugin_name=test_plugin|src_path=plugins_get|inputs=None|outputs=None|
        When I get plugin by id
        Then I get a plugin entity
        And It is equal to plugin created
