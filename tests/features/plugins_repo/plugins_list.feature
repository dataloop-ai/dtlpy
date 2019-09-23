Feature: Plugins repository list function testing

    Background: Initiate Platform Interface and create a project
        Given Platform Interface is initialized as dlp and Environment is set to development
        And There is a project by the name of "test_plugins_list"
        And Directory "plugins_list" is empty
        When I generate plugin by the name of "test_plugin" to "plugins_list"

    Scenario: list plugins when 0 exist
        When I list all project plugins
        Then I receive a list of "0" plugins

    @plugins.delete
    Scenario: list plugins when 1 exist
        When I push "first" plugin
            |package_id=None|plugin_name=None|src_path=plugins_list|inputs=None|outputs=None|
        Then I receive plugin entity
        And Plugin entity equals local plugin in "plugins_generate/to_compare_test_plugin"
        When I list all project plugins
        Then I receive a list of "1" plugins

