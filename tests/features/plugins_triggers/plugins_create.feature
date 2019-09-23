 Feature: Plugins repository push function testing

     Background: Initiate Platform Interface and create a project
         Given Platform Interface is initialized as dlp and Environment is set to development
         And There is a project by the name of "test_plugins_create"
         And Directory "plugins_create" is empty
         When I generate plugin by the name of "test_plugin" to "plugins_create"

    @plugins.delete
     Scenario: Create plugin
         When I push "first" plugin
             |package_id=None|plugin_name=test_plugin|src_path=plugins_create|inputs=None|outputs=None|
         Then I receive plugin entity
         And Plugin entity equals local plugin in "plugins_create"
