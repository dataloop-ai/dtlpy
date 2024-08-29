Feature: publish a dpk with model Integration

  Background:
    Given Platform Interface is initialized as dlp and Environment is set according to git branch
    And I create a project by the name of "dpk-intg-model"
    And I create a dataset by the name of "integ" in the project
    And I upload item in "0000000162.jpg" to dataset

  @DAT-76153
  Scenario: publishing a dpk with integrations optional true for model - Should be able to deploy model
    Given I fetch the dpk from 'app_with_integrations/module_model_integration.json' file
    And I remove the "value" from integration from the dpk in "integrations" component in index 0
    And I add "optional=True" to integration from the dpk in "integrations" component in index 0
    When I create a dummy model package by the name of "dummymodel" with entry point "main.py"
    And I create a model from package by the name of "model-num-1" with status "trained" in index "0"
    And I publish a dpk to the platform
    And I install the app
    And I get last model in project
    And I "deploy" the model
    Then I have a model service

