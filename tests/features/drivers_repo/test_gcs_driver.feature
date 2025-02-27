@rc_only
Feature: Driver repository testing - GCS

  Background: Initiate Platform Interface
    Given Platform Interface is initialized as dlp and Environment is set according to git branch
    And I create a project by the name of "drivers_gcs"
    And I create "gcs" integration with name "test-gcs-integration"

  @testrail-C4536790
  @datasets.delete
  @drivers.delete
  @DAT-49273
  Scenario: Create GCS Driver and stream Item - Should success
    When I create driver "gcs" with the name "test-gcs-driver"
      | key         | value          |
      | bucket_name | sdk_automation |
    Then I validate driver with the name "test-gcs-driver" is created
    When I create dataset "test-gcs" with driver entity
    And I sync dataset in context
    Then I validate driver dataset has "9" items
    And I stream Item by path "/img_1.jpg"

  @testrail-C4533706
  @drivers.delete
  @DAT-49273
  Scenario: Delete GCS Driver without connected dataset
    When I create driver "gcs" with the name "test-gcs-driver"
      | key         | value          |
      | bucket_name | sdk_automation |
    And I delete driver by the name "test-gcs-driver"
    Then I validate driver "test-gcs-driver" not longer in project drivers

  @testrail-C4533706
  @datasets.delete
  @drivers.delete
  @DAT-49273
  Scenario: Delete GCS Driver with connected dataset - Should return error
    When I create driver "gcs" with the name "test-gcs-driver"
      | key         | value          |
      | bucket_name | sdk_automation |
    Then I validate driver with the name "test-gcs-driver" is created
    When I create dataset "test-gcs" with driver entity
    And I sync dataset in context
    Then I validate driver dataset has "9" items
    When I delete driver by the name "test-gcs-driver"
    Then "BadRequest" exception should be raised

  @testrail-C4536790
  @datasets.delete
  @drivers.delete
  @DAT-49273
  Scenario: Create GCS Driver with path directory
    When I create driver "gcs" with the name "test-gcs-driver"
      | key         | value          |
      | bucket_name | sdk_automation |
      | path        | folder-1       |
    Then I validate driver with the name "test-gcs-driver" is created
    When I create dataset "test-gcs" with driver entity
    And I sync dataset in context
    Then I validate driver dataset has "4" items


  @datasets.delete
  @drivers.delete
  @DAT-51487
  Scenario: GCS Driver Actions - Upload item - stream item - delete item - Should upload and delete the item
    When I create driver "gcs" with the name "test-gcs-driver"
      | key                   | value          |
      | bucket_name           | sdk_automation |
    Then I validate driver with the name "test-gcs-driver" is created
    When I create dataset "test-gcs" with driver entity
    And I sync dataset in context
    Then I validate driver dataset has "9" items
    When I upload item in "0000000162.jpg"
    Then I stream Item by path "/0000000162.jpg"
    When I delete the item by name
    Then I wait "12"
    And I validate driver dataset has "9" items

  @datasets.delete
  @drivers.delete
  @DAT-87282
  Scenario: GCS Driver Actions - Stream and upload item using Dataloop platform the item should not be corrupted
    When I create driver "gcs" with the name "test-gcs-driver"
      | key                   | value          |
      | bucket_name           | sdk_automation |
    Then I validate driver with the name "test-gcs-driver" is created
    When I create dataset "test-gcs" with driver entity
    And I sync dataset in context
    Then I validate driver dataset has "9" items
    When I upload item in "0000000162.jpg"
    When I create dataset "test-gcs-to_delete" with driver entity
    And I sync dataset in context
    Then I use CRC to check original item in "0000000162.jpg" and streamed item from new dataset are not corrupted
    When I delete the item by name
    Then I wait "12"
    And I validate driver dataset has "9" items