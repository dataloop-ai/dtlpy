Feature: Models repository flow testing

  Background: Initiate Platform Interface and create a project
    Given Platform Interface is initialized as dlp and Environment is set according to git branch
    And I create a project by the name of "model_mgmt"
    And I create a dataset with a random name
    And I upload an item by the name of "test_item.jpg"
    When I upload labels to dataset
    And I upload "5" box annotation to item


  @DAT-50829
  Scenario: test model - failed
    Given I fetch the dpk from 'model_dpk/modelsDpks.json' file
    When I create a dummy model package by the name of "modelfaild" with entry point "failedmain.py"
    And I create a model from package by the name of "test-model-failed" with status "created" in index "0"
    And I publish a dpk to the platform
    And I install the app
    And i fetch the model by the name "test-model-failed"
    When i "train" the model
    Then model status should be "failed" with execution "True" that has function "train_model"


  @DAT-52904
  Scenario: test flow model - initPrams
    Given I fetch the dpk from 'model_dpk/modelsDpks.json' file
    When I create a dummy model package by the name of "initmodel" with entry point "main.py"
    And I create a model from package by the name of "test-model-init" with status "created" in index "0"
    And I publish a dpk to the platform
    And I install the app
    And i fetch the model by the name "test-model-init"
    When i train the model with init param model none
    Then model status should be "trained" with execution "True" that has function "train_model"
