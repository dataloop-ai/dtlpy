Feature: Driver repository create testing

  Background: Initiate Platform Interface
    Given Platform Interface is initialized as dlp and Environment is set according to git branch
    And I create a project by the name of "sdk_drivers"

  @testrail-C4533706
  @drivers.delete
  @integrations.delete
  Scenario: Create AWS Driver
    When  I create "aws" integration with name "test-aws-integration"
    And I create driver "aws" with the name "test-aws-driver"
      | key         | value          |
      | bucket_name | sdk-automation |
      | region      | eu-west-1      |
    Then I validate driver with the name "test-aws-driver" is created

  @testrail-C4533706
  @drivers.delete
  @integrations.delete
  Scenario: Create GCS Driver
    When  I create "gcs" integration with name "test-gcs-integration"
    And I create driver "gcs" with the name "test-gcs-driver"
      | key         | value          |
      | bucket_name | sdk_automation |
    Then I validate driver with the name "test-gcs-driver" is created

  @testrail-C4533706
  @drivers.delete
  @integrations.delete
  Scenario: Create Azure Driver
    When  I create "azureblob" integration with name "test-azure-integration"
    And I create driver "azureblob" with the name "test-azure-driver"
      | key         | value          |
      | bucket_name | test-container |
    Then I validate driver with the name "test-azure-driver" is created