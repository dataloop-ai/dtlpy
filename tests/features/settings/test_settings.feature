Feature: Settings Context

  Background: Background name
    Given Platform Interface is initialized as dlp and Environment is set according to git branch

  @testrail-C4529105
  Scenario: check box rotation settings
    When I create two project  and datasets by the name of "to-delete-test-settings_test1" "to-delete-test-settings_test2"
    And I upload item in "0000000162.jpg" to both datasets
    And i upload annotations to both items
    And add settings to the first project
    Then check if geo in the first item and in the second are difference



