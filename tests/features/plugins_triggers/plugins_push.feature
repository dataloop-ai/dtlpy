Feature: Plugins repository push function testing

    Background: Initiate Platform Interface and create a project
        Given Platform Interface is initialized as dlp and Environment is set to development
        And There is a project by the name of "test_plugins_push"
        And Directory "plugins_push" is empty
        When I generate plugin by the name of "test_plugin" to "plugins_push"

    @plugins.delete
    Scenario: Push local plugin - no params
        When I push "first" plugin
            |package_id=None|plugin_name=None|src_path=plugins_push|inputs=None|outputs=None|
        Then I receive plugin entity
        And Plugin entity equals local plugin in "plugins_generate/to_compare_test_plugin"
        When I modify python file - (change version) in path "plugins_push/main.py"
        And I push "second" plugin
            |package_id=None|plugin_name=None|src_path=plugins_push|inputs=None|outputs=None|
        Then I receive another plugin entity
        And 1st plugin and 2nd plugin only differ in package id
