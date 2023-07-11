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
  Scenario: Create GCS Driver
    When I create driver "gcs" with the name "test-gcs-driver"
      | key         | value          |
      | bucket_name | sdk_automation |
    Then I validate driver with the name "test-gcs-driver" is created
    When I create dataset "test-gcs" with driver entity
    And I sync dataset in context
    Then I validate driver dataset has "9" items

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