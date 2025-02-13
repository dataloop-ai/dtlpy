@rc_only
Feature: Driver repository testing - AWS

  Background: Initiate Platform Interface
    Given Platform Interface is initialized as dlp and Environment is set according to git branch
    And I create a project by the name of "drivers_aws"
    And I create "s3" integration with name "test-aws-integration"


  @testrail-C4533706
  @datasets.delete
  @drivers.delete
  @DAT-49271
  Scenario: Create AWS Driver - Sync items - Should success
    When I create driver "s3" with the name "test-aws-driver"
      | key         | value                        |
      | bucket_name | qa-sdk-automation-access-key |
      | region      | eu-west-1                    |
    Then I validate driver with the name "test-aws-driver" is created
    When I create dataset "test-aws" with driver entity
    And I sync dataset in context
    Then I validate driver dataset has "9" items

  @testrail-C4533706
  @drivers.delete
  @DAT-49271
  Scenario: Delete AWS Driver without connected dataset
    When I create driver "s3" with the name "test-aws-driver"
      | key         | value                        |
      | bucket_name | qa-sdk-automation-access-key |
      | region      | eu-west-1                    |
    And I delete driver by the name "test-aws-driver"
    Then I validate driver "test-aws-driver" not longer in project drivers

  @testrail-C4533706
  @datasets.delete
  @drivers.delete
  @DAT-49271
  Scenario: Delete AWS Driver with connected dataset - Should return error
    When I create driver "s3" with the name "test-aws-driver"
      | key         | value                        |
      | bucket_name | qa-sdk-automation-access-key |
      | region      | eu-west-1                    |
    Then I validate driver with the name "test-aws-driver" is created
    When I create dataset "test-aws" with driver entity
    And I sync dataset in context
    Then I validate driver dataset has "9" items
    When I delete driver by the name "test-aws-driver"
    Then "BadRequest" exception should be raised


  @testrail-C4533706
  @datasets.delete
  @drivers.delete
  @DAT-49271
  Scenario: Create AWS Driver with path directory
    When I create driver "s3" with the name "test-aws-driver"
      | key         | value                        |
      | bucket_name | qa-sdk-automation-access-key |
      | region      | eu-west-1                    |
      | path        | folder-1                     |
    Then I validate driver with the name "test-aws-driver" is created
    When I create dataset "test-aws" with driver entity
    And I sync dataset in context
    Then I validate driver dataset has "4" items


  @testrail-C4533706
  @datasets.delete
  @drivers.delete
  @DAT-49271
  Scenario: Create AWS-sts Driver
    Given I create "aws-sts" integration with name "test-aws-sts-integration"
    When I create driver "s3" with the name "test-aws-sts-driver"
      | key         | value                 |
      | bucket_name | qa-sdk-sts-automation |
      | region      | eu-west-1             |
    Then I validate driver with the name "test-aws-sts-driver" is created
    When I create dataset "test-aws" with driver entity
    And I sync dataset in context
    Then I validate driver dataset has "9" items

  @datasets.delete
  @drivers.delete
  @DAT-85745
  Scenario: Create AWS Driver - Stream and upload item - Should success
    When I create driver "s3" with the name "test-aws-driver"
      | key         | value                        |
      | bucket_name | qa-sdk-automation-access-key |
      | region      | eu-west-1                    |
    Then I validate driver with the name "test-aws-driver" is created
    When I create dataset "test-aws" with driver entity
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
  @DAT-86789
  Scenario: Create AWS Driver - Stream and upload item using Dataloop platform the item should not be corrupted
    When I create driver "s3" with the name "test-aws-driver"
      | key         | value                        |
      | bucket_name | qa-sdk-automation-access-key |
      | region      | eu-west-1                    |
    Then I validate driver with the name "test-aws-driver" is created
    When I create dataset "test-aws" with driver entity
    And I sync dataset in context
    Then I validate driver dataset has "9" items
    When I upload item in "0000000162.jpg"
    When I create dataset "test-aws-to_delete" with driver entity
    And I sync dataset in context
    Then I use CRC to check original item in "0000000162.jpg" and streamed item from new dataset are not corrupted
    When I delete the item by name
    Then I wait "12"
    And I validate driver dataset has "9" items

  @datasets.delete
  @drivers.delete
  @DAT-87206
  Scenario: Create AWS Driver - and multiple sync it to a dataset
    When I create driver "s3" with the name "test-aws-driver"
      | key         | value                        |
      | bucket_name | qa-sdk-automation-access-key |
      | region      | eu-west-1                    |
    Then I validate driver with the name "test-aws-driver" is created
    When I create dataset "test-aws" with driver entity
    And I sync dataset in context with is "False"
    Then I wait "0.5"
    When I sync dataset in context with is "False"
    Then I receive error with status code "423"
    Then "as it is already being synced." in error message
    Then I wait "5"