Feature: publish a dpk

  Background:
    Given Platform Interface is initialized as dlp and Environment is set according to git branch
    And I create a project by the name of "test_app_ins"
    And I create a dataset by the name of "model" in the project


  @DAT-50097
  Scenario: Publishing a dpk with model adapter
    Given I fetch the dpk from 'apps/app_include_models_adapter.json' file
    When I add the context.dataset to the dpk model
    And I publish a dpk to the platform
    And  I install the app
    And I set the model in the context
    Then Model object with the same name should be exist
    And model status should be "deployed" with execution "False" that has function "run"
    And Model module_name should be "my-adapter"
    And I uninstall the app

  @DAT-50097
  Scenario: Publishing a dpk with model with subset
    Given I fetch the dpk from 'apps/app_include_filters_models.json' file
    When I add the context.dataset to the dpk model
    And I set code path "models_flow" to context
    And I pack directory by name "model_flow"
    And I add codebase to dpk
    And I publish a dpk to the platform
    And  I install the app
    And I set the model in the context
    Then Model object with the same name should be exist
    And Model status should be "deployed" with execution "False" that has function "run"
    And I uninstall the app

  @DAT-50162
  Scenario: Publishing a dpk with model - Should be able to evaluate
    Given I fetch the dpk from 'apps/app_include_filters_models.json' file
    And I upload an item by the name of "test_item.jpg"
    When I upload labels to dataset
    And I upload "5" box annotation to item
    When I add the context.dataset to the dpk model
    And I set code path "models_flow" to context
    And I pack directory by name "model_flow"
    And I add codebase to dpk
    And I publish a dpk to the platform
    And  I install the app
    And I set the model in the context
    Then Model object with the same name should be exist
    And model status should be "deployed" with execution "False" that has function "run"
    When i "evaluate" the model
    Then model status should be "deployed" with execution "True" that has function "evaluate_model"
    And Dataset has a scores file
    When i call the precision recall api
    Then i should get a json response


  @DAT-50097
  Scenario: Publishing a dpk with model and compute
    Given I fetch the dpk from 'apps/app_include_compute_models.json' file
    When I add the context.dataset to the dpk model
    And I set code path "models_flow" to context
    And I pack directory by name "model_flow"
    And I add codebase to dpk
    And I publish a dpk to the platform
    And  I install the app
    And I set the model in the context
    Then Model object with the same name should be exist
    When i "deploy" the model
    Then i have a model service
    Then I compare service config with dpk compute configuration for the operation "deploy"