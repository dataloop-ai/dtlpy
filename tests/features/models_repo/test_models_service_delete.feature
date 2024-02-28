Feature: Models repository delete flow testing

  Background: Initiate Platform Interface and create a project
    Given Platform Interface is initialized as dlp and Environment is set according to git branch
    And I create a project by the name of "model_mgmt"
    And I create a dataset with a random name
    And I upload an item by the name of "test_item.jpg"
    When I upload labels to dataset
    And I upload "5" box annotation to item

  @DAT-56475
  Scenario: test model delete services
    Given I fetch the dpk from 'model_dpk/modelsDpks.json' file
    When I create a dummy model package by the name of "dummymodel" with entry point "main.py"
    And I create a model from package by the name of "test-model" with status "created" in index "0"
    And I publish a dpk to the platform
    And I install the app
    And i fetch the model by the name "test-model"
    When i "train" the model
    Then service metadata has a model id and operation "train"
    Then model status should be "trained" with execution "True" that has function "train_model"
    When I get service by id
    Then Service is archived

    When i "deploy" the model
    Then model status should be "deployed" with execution "False" that has function "None"
    And i have a model service
    When I delete service by "id"
    When I get service by id
    Then Service is archived

    When i "evaluate" the model
    Then model status should be "trained" with execution "True" that has function "evaluate_model"
    And service metadata has a model id and operation "evaluate"
    When I delete service by "id"
    When I get service by id
    Then Service is archived