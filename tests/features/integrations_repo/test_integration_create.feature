@rc_only
Feature: Integrations repository create testing

  Background: Initiate Platform Interface
    Given Platform Interface is initialized as dlp and Environment is set according to git branch
    And I create a project by the name of "sdk_integrations"

  @testrail-C4533705
  @DAT-46529
  Scenario: Create AWS integration
    Given I create "s3" integration with name "test-aws-integration"
    Then I validate integration with the name "test-aws-integration" is created

  @testrail-C4533705
  @DAT-46529
  Scenario: Create GCS integration
    Given I create "gcs" integration with name "test-gcs-integration"
    Then I validate integration with the name "test-gcs-integration" is created

  @testrail-C4533705
  @DAT-46529
  Scenario: Create Azure-blob integration
    Given I create "azureblob" integration with name "test-azure-integration"
    Then I validate integration with the name "test-azure-integration" is created

  @testrail-C4533705
  @DAT-46529
  Scenario: Create Azure-gen2 integration
    Given I create "azuregen2" integration with name "test-azure-gen2-integration"
    Then I validate integration with the name "test-azure-gen2-integration" is created


  @testrail-C4533705
  @DAT-46529
  Scenario: Create AWS-sts integration
    Given I create "aws-sts" integration with name "test-aws-sts-integration"
    Then I validate integration with the name "test-aws-sts-integration" is created