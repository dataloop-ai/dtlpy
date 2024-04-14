Feature: Model repository query testing

  Background: Initiate Platform Interface and create a project
    Given Platform Interface is initialized as dlp and Environment is set according to git branch
    And I create a project by the name of "models_list"
    And I create a dataset by the name of "models_dataset" in the project

  @testrail-C4525320
  @DAT-46549
  Scenario: List by model name
    Given I fetch the dpk from 'model_dpk/modelsDpks.json' file
    When I create a dummy model package by the name of "dummymodel" with entry point "main.py"
    And I create a model from package by the name of "model-num-1" with status "trained" in index "0"
    And I create a model from package by the name of "model-num-2" with status "trained" in index "1"
    And I add the context.dataset to the dpk model
    And I publish a dpk to the platform
    And I install the app
    When I list models with filter field "name" and values "model-num-1"
    Then I get "1" entities


