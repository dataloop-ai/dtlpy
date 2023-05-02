Feature: Settings Context

  Background: Background name
    Given Platform Interface is initialized as dlp and Environment is set according to git branch

  @testrail-C4529105
  Scenario: check box rotation settings
    When I create two project  and datasets by the name of "to-delete-test-settings_test1" "to-delete-test-settings_test2"
    And I upload item in "0000000162.jpg" to both datasets
    And i upload annotations to both items
    And add settings to the project
    Then check if geo in the first item and in the second are difference

  @testrail-C4532534
  Scenario: check get setting by id
    Given I create a project by the name of "to-delete-test-setting-get-id"
    When add settings to the project
    And I get setting by "id"
    Then I check setting got is equal to the one created

  @testrail-C4532533
  Scenario: check get setting by name
    When I create a project by the name of "to-delete-test-setting-get-name"
    When add settings to the project
    And I get setting by "name"
    Then I check setting got is equal to the one created

  @DAT-46364
  Scenario Outline: check settings type validation
    When I create a project by the name of "to-delete-test-setting-validate_type"
    When I add settings to the project with wrong "<value>" type
    Then I expect the correct exception to be thrown
    Examples: Type
      | value   |
      | 'boaz'  |
      | 123     |