Feature: Projects repository create integration testing

  Background: Background name
    Given Platform Interface is initialized as dlp and Environment is set according to git branch
    And I create a project by the name of "integration-key_value"

  @testrail-C4532976
  @integrations.delete
  Scenario: Create key value integration in project
    When I create "key_value" integration with name "sdk_automation_key_value"
    Then I validate integration with the name "sdk_automation_key_value" is created


  @testrail-C4532976
  Scenario: Delete key value integration in project
    When I create "key_value" integration with name "sdk_automation_to_delete"
    And I delete integration in context
    Then I validate integration "sdk_automation_to_delete" not in integrations list
