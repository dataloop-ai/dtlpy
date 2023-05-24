@rc_only
Feature: Driver repository testing - AZURE

  Background: Initiate Platform Interface
    Given Platform Interface is initialized as dlp and Environment is set according to git branch
    And I create a project by the name of "drivers_azure"
    And  I create "azureblob" integration with name "test-azure-integration"

  @testrail-C4536789
  @datasets.delete
  @drivers.delete
  Scenario: Create Azure Blob Driver
    When I create driver "azureblob" with the name "test-azure-driver"
      | key         | value          |
      | bucket_name | sdk-automation |
    Then I validate driver with the name "test-azure-driver" is created
    When I create dataset "test-azure" with driver entity
    And I sync dataset in context
    Then I validate driver dataset has "9" items

  @testrail-C4533706
  @drivers.delete
  Scenario: Delete Azure Driver without connected dataset
    When I create driver "azureblob" with the name "test-azure-driver"
      | key         | value          |
      | bucket_name | sdk-automation |
    And I delete driver by the name "test-azure-driver"
    Then I validate driver "test-azure-driver" not longer in project drivers


  @testrail-C4533706
  @datasets.delete
  @drivers.delete
  Scenario: Delete Azure Driver with connected dataset - Should return error
    When I create driver "azureblob" with the name "test-azure-driver"
      | key         | value          |
      | bucket_name | sdk-automation |
    Then I validate driver with the name "test-azure-driver" is created
    When I create dataset "test-azure" with driver entity
    And I sync dataset in context
    Then I validate driver dataset has "9" items
    When I delete driver by the name "test-azure-driver"
    Then "BadRequest" exception should be raised


  @testrail-C4536789
  @datasets.delete
  @drivers.delete
  Scenario: Create Azure DatalakeGe2 Driver
    Given I create "azuregen2" integration with name "test-azure-gen2-integration"
    When I create driver "azureDatalakeGen2" with the name "test-azure-gen2-driver"
      | key         | value               |
      | bucket_name | sdk-automation-gen2 |
    Then I validate driver with the name "test-azure-gen2-driver" is created
    When I create dataset "azure-datalake-gen2" with driver entity
    And I sync dataset in context
    Then I validate driver dataset has "9" items

  @testrail-C4536789
  @datasets.delete
  @drivers.delete
  Scenario: Create Azure Blob Driver with path directory
    When I create driver "azureblob" with the name "test-azure-driver"
      | key         | value          |
      | bucket_name | sdk-automation |
      | path        | folder-1       |
    Then I validate driver with the name "test-azure-driver" is created
    When I create dataset "test-azure" with driver entity
    And I sync dataset in context
    Then I validate driver dataset has "4" items