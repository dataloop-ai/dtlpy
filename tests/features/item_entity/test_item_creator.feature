Feature: Item Creator testing

  Background: Initiate Platform Interface
    Given Platform Interface is initialized as dlp and Environment is set according to git branch
    And I create a project by the name of "item_creator_project"

  @datasets.delete
  @drivers.delete
  @DAT-85611
  Scenario: Import an item from AWS and validate it has a creator
    Given I create "s3" integration with name "s3-test-qa"
    When I create driver "s3" with the name "test-item-creator-aws"
      | key         | value                        |
      | bucket_name | qa-sdk-automation-access-key |
      | region      | eu-west-1                    |
    Then I validate driver with the name "test-item-creator-aws" is created
    When I create dataset "test-aws" with driver entity
    When I import item "img_1.jpg" from "root"


  @datasets.delete
  @drivers.delete
  @DAT-85610
  Scenario: Import an item from GCS and validate it has a creator
    Given I create "gcs" integration with name "gcs-test-qa"
    When I create driver "gcs" with the name "test-item-creator-gcs"
      | key         | value          |
      | bucket_name | sdk_automation |
      | region      | eu-west-1      |
    Then I validate driver with the name "test-item-creator-gcs" is created
    When I create dataset "test-gcs" with driver entity
    When I import item "img_9.jpg" from "folder-1"


  @datasets.delete
  @drivers.delete
  @DAT-85822
  Scenario: Import an item from AZURE and validate it has a creator
    Given I create "azureblob" integration with name "azure-test-qa"
    When I create driver "azureblob" with the name "test-azure-driver"
      | key         | value          |
      | bucket_name | sdk-automation |
    Then I validate driver with the name "test-azure-driver" is created
    When I create dataset "test-azure" with driver entity
    When I import item "img_1.jpg" from "root"
