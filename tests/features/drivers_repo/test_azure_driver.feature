@rc_only
Feature: Driver repository testing - AZURE

  Background: Initiate Platform Interface
    Given Platform Interface is initialized as dlp and Environment is set according to git branch
    And I create a project by the name of "drivers_azure"
    And  I create "azureblob" integration with name "test-azure-integration"

  @testrail-C4536789
  @datasets.delete
  @drivers.delete
  @DAT-49272
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
  @DAT-49272
  Scenario: Delete Azure Driver without connected dataset
    When I create driver "azureblob" with the name "test-azure-driver"
      | key         | value          |
      | bucket_name | sdk-automation |
    And I delete driver by the name "test-azure-driver"
    Then I validate driver "test-azure-driver" not longer in project drivers


  @testrail-C4533706
  @datasets.delete
  @drivers.delete
  @DAT-49272
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
  @DAT-49272
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
  @DAT-49272
  Scenario: Create Azure Blob Driver with path directory
    When I create driver "azureblob" with the name "test-azure-driver"
      | key         | value          |
      | bucket_name | sdk-automation |
      | path        | folder-1       |
    Then I validate driver with the name "test-azure-driver" is created
    When I create dataset "test-azure" with driver entity
    And I sync dataset in context
    Then I validate driver dataset has "4" items


  @datasets.delete
  @drivers.delete
  @DAT-85746
  Scenario: Create Azure Blob Driver - Stream and upload item - Should success
    When I create driver "azureblob" with the name "test-azure-driver"
      | key         | value          |
      | bucket_name | sdk-automation |
    Then I validate driver with the name "test-azure-driver" is created
    When I create dataset "test-azure" with driver entity
    And I sync dataset in context
    Then I validate driver dataset has "9" items
    And I stream Item by path "/img_1.jpg"
    When I upload item in "0000000162.jpg"
    Then I stream Item by path "/0000000162.jpg"
    When I delete the item by name
    Then I wait "12"
    And I validate driver dataset has "9" items

  @datasets.delete
  @drivers.delete
  @DAT-85747
  Scenario: Create Azure DatalakeGe2 Driver - Stream and upload item - Should success
    Given I create "azuregen2" integration with name "test-azure-gen2-integration"
    When I create driver "azureDatalakeGen2" with the name "test-azure-gen2-driver"
      | key         | value               |
      | bucket_name | sdk-automation-gen2 |
    Then I validate driver with the name "test-azure-gen2-driver" is created
    When I create dataset "azure-datalake-gen2" with driver entity
    And I sync dataset in context
    Then I validate driver dataset has "9" items
    And I stream Item by path "/img_1.jpg"
    When I upload item in "0000000162.jpg"
    Then I stream Item by path "/0000000162.jpg"
    When I delete the item by name
    Then I wait "12"
    And I validate driver dataset has "9" items

  @datasets.delete
  @drivers.delete
  @DAT-87284
  Scenario: Create Azure Blob Driver - Stream and upload item using Dataloop platform the item should not be corrupted
    When I create driver "azureblob" with the name "test-azure-driver"
      | key         | value          |
      | bucket_name | sdk-automation |
    Then I validate driver with the name "test-azure-driver" is created
    When I create dataset "test-azure" with driver entity
    And I sync dataset in context
    Then I validate driver dataset has "9" items
    When I upload item in "0000000162.jpg"
    When I create dataset "test-azure-to_delete" with driver entity
    And I sync dataset in context
    Then I use CRC to check original item in "0000000162.jpg" and streamed item from new dataset are not corrupted
    When I delete the item by name
    Then I wait "12"
    And I validate driver dataset has "9" items