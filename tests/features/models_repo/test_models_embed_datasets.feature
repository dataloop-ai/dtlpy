Feature: Models repository embed datasets testing

  Background: Initiate Platform Interface and create a project
    Given Platform Interface is initialized as dlp and Environment is set according to git branch
    And I create a project by the name of "model_mgmt-embed"
    And I create a dataset with a random name
    And I upload an item by the name of "test_item.jpg"
    When I upload labels to dataset
    And I upload "5" box annotation to item
    Given I create a dataset with a random name
    And I upload an item by the name of "test_item.jpg"
    When I upload labels to dataset
    And I upload "5" box annotation to item

  @DAT-81076
  Scenario: test model with embedded datasets
    Given I fetch the dpk from 'model_dpk/modelsDpks.json' file
    When I create a dummy model package by the name of "dummymodel" with entry point "main.py"
    And I create a model from package by the name of "test-model" with status "trained" in index "0"
    And I publish a dpk to the platform
    And I install the app
    And i fetch the model by the name "test-model"
    When i "deploy" the model
    Then model status should be "deployed" with execution "False" that has function "None"
    When I run model embed datasets
    Then command status is "success"
    And model service has "2" executions and "2" triggers
    Given I upload an item by the name of "test_item2.jpg"
    Then model service has "3" executions and "2" triggers
    And i clean the project

  @DAT-81076
  Scenario: test model with embedded datasets twice
    Given I fetch the dpk from 'model_dpk/modelsDpks.json' file
    When I create a dummy model package by the name of "dummymodel" with entry point "main.py"
    And I create a model from package by the name of "test-model" with status "trained" in index "0"
    And I publish a dpk to the platform
    And I install the app
    And i fetch the model by the name "test-model"
    When i "deploy" the model
    Then model status should be "deployed" with execution "False" that has function "None"
    When I run model embed datasets
    Then command status is "success"
    And model service has "4" executions and "4" triggers
    When I run model embed datasets
    Then command status is "success"
    And model service has "8" executions and "4" triggers
    And i clean the project


  @DAT-81076
  Scenario: test model with embedded datasets - command failed
    Given I fetch the dpk from 'model_dpk/modelsDpks.json' file
    When I create a dummy model package by the name of "dummymodel" with entry point "main.py"
    And I create a model from package by the name of "test-model" with status "trained" in index "0"
    And I publish a dpk to the platform
    And I install the app
    And i fetch the model by the name "test-model"
    When i "deploy" the model
    Then model status should be "deployed" with execution "False" that has function "None"
    When i change model status to "trained"
    When I run model embed datasets
    Then command massage is in model
    And model service has "0" executions and "0" triggers
    And i clean the project