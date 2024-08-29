@qa-nightly
@rc_only
Feature: Projects repository create integration testing

  Background: Background name
    Given Platform Interface is initialized as dlp and Environment is set according to git branch
    And I create a project by the name of "integration-key_value"

  @testrail-C4532976
  @DAT-46597
  Scenario: Create key value integration in project
    Given I create "key_value" integration with name "sdk_automation_key_value"
    Then I validate integration with the name "sdk_automation_key_value" is created

  @testrail-C4532976
  @DAT-46597
  Scenario: Delete key value integration in project
    Given I create "key_value" integration with name "sdk_automation_to_delete"
    When I delete integration in context
    Then I validate integration not in integrations list by context.integration_name

  @DAT-76494
  Scenario: Create key value integration in project with valid key-value metadata
    When I create "key_value" integration with name "sdk_automation_key_value_valid" and metadata "{'provider': 'test_provider', 'ref': 'test_ref'}"
    Then I validate integration with the name "sdk_automation_key_value_valid" is created

  @DAT-76495
  Scenario: Create key value integration in project with invalid key-value metadata
    When I create "key_value" integration with name "sdk_automation_key_value_invalid" and metadata "{'hello': 'world', 'key': 'key'}"
    Then I receive error with status code "400"
    And "Invalid metadata fields for key-value integration" in error message

  @DAT-76497
  Scenario: Create gcp-cross integration in project with key-value metadata
    When I create "gcp-cross" integration with name "sdk_automation_gcp_cross_invalid" and metadata "{'provider': 'test_provider', 'ref': 'test_ref'}"
    Then I receive error with status code "400"
    And "Invalid input specified" in error message
