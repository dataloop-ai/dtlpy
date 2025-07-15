Feature: Models repository update services testing

  Background: Initiate Platform Interface and create a project
    Given Platform Interface is initialized as dlp and Environment is set according to git branch
    And I create a project by the name of "model_mgmt_services"
    And I create a dataset with a random name
    And I upload an item by the name of "test_item.jpg"
    When I upload labels to dataset
    And I upload "5" box annotation to item

  @DAT-86051
  Scenario: test flow model services update
    Given I fetch the dpk from 'model_dpk/modelsDpks.json' file
    When I create a dummy model package by the name of "dummymodel" with entry point "main.py"
    And I create a model from package by the name of "test-model" with status "pre-trained" in index "0"
    And I publish a dpk to the platform
    And I install the app
    And i fetch the model by the name "test-model"
    When i "deploy" the model
    When i "evaluate" the model
    When I update the model config with the following
      | key   | value    |
      | param | new_value|
    Then model config should be updated with the following
      | key   | value    |
      | param | new_value|
    When I wait "5"
    When model "reloadServices" command success
    Then all relevant model services should be updated

