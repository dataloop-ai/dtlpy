@rc_only
Feature: Dataset storage testing

  Background: Initiate Platform Interface and create a project
    Given Platform Interface is initialized as dlp and Environment is set according to git branch
    And I create a project by the name of "datasets_list"

  @testrail-C4523089
  @datasets.delete
  @drivers.delete
  @DAT-54449
  Scenario: List only storage datasets by driver id
    Given I create "s3" integration with name "test-aws-integration"
    And I create a dataset with a random name
    When I create driver "s3" with the name "test-aws-driver"
      | key         | value          |
      | bucket_name | sdk-automation |
      | region      | eu-west-1      |
    Then I validate driver with the name "test-aws-driver" is created
    When I create dataset "test-aws" with driver entity
    Given I init Filters() using the given params
      | Parameter | Value   |
      | resource  | DATASET |
    When I call Filters.add() using the given params
      | Parameter | Value     |
      | field     | driver    |
      | values    | driver.id |
      | operator  | IN        |
    And I list datasets using context.filter
    Then I receive a datasets list of "1" dataset
