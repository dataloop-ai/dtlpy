Feature: Models repository integration testing

  Background: Initiate Platform Interface and create a project
    Given Platform Interface is initialized as dlp and Environment is set according to git branch
    And I create a project by the name of "model_mgmt"
    And I create a dataset with a random name
    And I upload an item by the name of "test_item.jpg"
    When I upload labels to dataset
    And I upload "5" box annotation to item


  @DAT-70200
  Scenario: test integration
    Given I create "key_value" integration with name "init_integrations"
    Given I fetch the dpk from 'apps/app_model_init_intg.json' file
    When I add integration to dpk
    When I set code path "init_integrations" to context
    When I create a dummy model package by the name of "dummymodel" with entry point "main_model.py"
    And I create a model from package by the name of "test-model" with status "created" in index "0"
    And I publish a dpk to the platform
    And I install the app
    And i fetch the model by the name "test-model"
    When i "train" the model
    Then service metadata has a model id and operation "train"
    Then model status should be "trained" with execution "True" that has function "train_model"
    When I delete integration in context
