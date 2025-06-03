@rc_only
Feature: Driver repository testing - MinIO

  Background: Initiate Platform Interface
    Given Platform Interface is initialized as dlp and Environment is set according to git branch
    And I create a project by the name of "drivers_minio"
    And I create "s3_minio" integration with name "test-minio-integration"


  @datasets.delete
  @drivers.delete
  @DAT-94519
  Scenario: Create MinIO Driver - Sync items - Should success
    When I create driver "s3" with the name "test-minio-driver"
      | key         | value                        |
      | bucket_name | qa-automation-tests          |
      | region      | eu-west-1                    |
      | end_point   | ENV_MINIO_ENDPOINT           |
    Then I validate driver with the name "test-minio-driver" is created
    When I create dataset "test-minio" with driver entity
    And I sync dataset in context
    Then I validate driver dataset has "16" items

  @drivers.delete
  @drivers.delete
  @DAT-94520
  Scenario: Delete MinIO Driver without connected dataset
    When I create driver "s3" with the name "test-minio-driver"
      | key         | value                        |
      | bucket_name | qa-automation-tests          |
      | region      | eu-west-1                    |
      | end_point   | ENV_MINIO_ENDPOINT           |
    And I delete driver by the name "test-minio-driver"
    Then I validate driver "test-minio-driver" not longer in project drivers

  @datasets.delete
  @drivers.delete
  @DAT-94522
  Scenario: Delete MinIO Driver with connected dataset - Should return error
    When I create driver "s3" with the name "test-minio-driver"
      | key         | value                        |
      | bucket_name | qa-automation-tests          |
      | region      | eu-west-1                    |
      | end_point   | ENV_MINIO_ENDPOINT           |
    Then I validate driver with the name "test-minio-driver" is created
    When I create dataset "test-minio" with driver entity
    And I sync dataset in context
    Then I validate driver dataset has "16" items
    When I delete driver by the name "test-minio-driver"
    Then "BadRequest" exception should be raised


  @datasets.delete
  @drivers.delete
  @DAT-94523
  Scenario: Create MinIO Driver with path directory
    When I create driver "s3" with the name "test-minio-driver"
      | key         | value                        |
      | bucket_name | qa-automation-tests          |
      | region      | eu-west-1                    |
      | end_point   | ENV_MINIO_ENDPOINT           |
      | path        | numbers                      |
    Then I validate driver with the name "test-minio-driver" is created
    When I create dataset "test-minio" with driver entity
    And I sync dataset in context
    Then I validate driver dataset has "9" items