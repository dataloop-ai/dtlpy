Feature: Plugins Flow

    Background: Initiate Platform Interface and create a project
        Given Platform Interface is initialized as dlp and Environment is set to development
        And There is a project by the name of "test_plugins_flow"
        And I create a dataset with a random name
        And Directory "plugin_flow/plugin_directory" is empty

    @deployments.delete
    @plugins.delete
    Scenario: Flow
        When I generate plugin by the name of "None" to "plugin_flow/plugin_directory"
        And I upload a file in path "plugin_flow/plugin_assets/picture1.jpg"
        And I copy all relevant files from "plugin_flow/plugin_assets" to "plugin_flow/plugin_directory"
        And I test local plugin in "plugin_flow/plugin_directory"
        And I push and deploy pluign in "plugin_flow/plugin_directory"
        And I upload item in "plugin_flow/plugin_assets/picture2.jpg" to dataset
        Then Item "1" annotations equal annotations in "plugin_flow/plugin_assets/annotations1.json"
        And Item "2" annotations equal annotations in "plugin_flow/plugin_assets/annotations2.json"