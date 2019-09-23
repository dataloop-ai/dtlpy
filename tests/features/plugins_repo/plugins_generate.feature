Feature: Plugins repository generate function testing

  Background: Initiate Platform Interface and create a project
    Given Platform Interface is initialized as dlp and Environment is set to development
    And There is a project by the name of "test_plugins_generate"

  Scenario: Generate plugin - no given path - nameless
    Given Directory "plugins_generate/to_generate" is empty
    And cwd is "plugins_generate/to_generate"
    When I generate plugin by the name of "None" to "None"
    And cwd goes back to original
    Then Plugin local files in "plugins_generate/to_generate" equal plugin local files in "plugins_generate/to_compare_nameless"

  Scenario: Generate plugin - no given path - by name
    Given Directory "plugins_generate/to_generate" is empty
    And cwd is "plugins_generate/to_generate"
    When I generate plugin by the name of "test_plugin" to "None"
    And cwd goes back to original
    Then Plugin local files in "plugins_generate/to_generate" equal plugin local files in "plugins_generate/to_compare_test_plugin"

  Scenario: Generate plugin by name
    Given Directory "plugins_generate/to_generate" is empty
    When I generate plugin by the name of "test_plugin" to "plugins_generate/to_generate"
    Then Plugin local files in "plugins_generate/to_generate" equal plugin local files in "plugins_generate/to_compare_test_plugin"

  Scenario: Generate plugin - nameless
    Given Directory "plugins_generate/to_generate" is empty
    When I generate plugin by the name of "None" to "plugins_generate/to_generate"
    Then Plugin local files in "plugins_generate/to_generate" equal plugin local files in "plugins_generate/to_compare_nameless"
