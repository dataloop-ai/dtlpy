Feature: App Verification error

  Background:
    Given Platform Interface is initialized as dlp and Environment is set according to git branch
    And I create a project by the name of "model_mgmt"
    And I create a dataset with a random name
    And I upload an item by the name of "test_item.jpg"
    When I upload labels to dataset
    And I upload "5" box annotation to item


  @DAT-83113
  Scenario: DPK model with wrong values - App should failed to installed with correct error
    Given I fetch the dpk from 'model_dpk/modelsDpks.json' file and update dpk with params 'True'
      | key                            | value |
      | components.models.0.outputType | Image |
    When I create a dummy model package by the name of "dummymodel" with entry point "main.py"
    And I create a model from package by the name of "test-model" with status "created" in index "0"
    And I publish a dpk to the platform
    And I try to install the app
    Then "FailedDependency" exception should be raised
    And app is not installed in the project
    And "error installing an app: Validation Failed" in error message
    And "model.outputType" in error message
    And ""value":"Image"" in error message
