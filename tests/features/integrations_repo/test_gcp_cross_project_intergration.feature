@rc_only
Feature: Integrations repository create testing

  Background: Initiate Platform Interface
    Given Platform Interface is initialized as dlp and Environment is set according to git branch
    And I create a project by the name of "sdk_cross_integrations"

  @DAT-52122
  Scenario: Create GCP-cross-project integration and validate service account created
    Given I create "gcp-cross" integration with name "test-gcp-cross-project-integration"
    Then I validate integration with the name "test-gcp-cross-project-integration" is created
    And I validate gcp-cross-project has correct service account pattern