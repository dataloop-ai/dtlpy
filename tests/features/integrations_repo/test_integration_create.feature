Feature: Integrations repository create testing

  Background: Initiate Platform Interface
    Given Platform Interface is initialized as dlp and Environment is set according to git branch
    And I create a project by the name of "sdk_integrations"

  @testrail-C4533705
  @integrations.delete
  Scenario: Create AWS integration
    When  I create "aws" integration with name "test-aws-integration"
    Then  I validate integration with the name "test-aws-integration" is created

  @testrail-C4533705
  @integrations.delete
  Scenario: Create GCS integration
    When  I create "gcs" integration with name "test-gcs-integration"
    Then  I validate integration with the name "test-gcs-integration" is created

  @testrail-C4533705
  @integrations.delete
  Scenario: Create Azure-blob integration
    When  I create "azureblob" integration with name "test-azure-integration"
    Then  I validate integration with the name "test-azure-integration" is created