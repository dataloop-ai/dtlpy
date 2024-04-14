Feature: publish a dpk

  Background:
    Given Platform Interface is initialized as dlp and Environment is set according to git branch
    And I create a project by the name of "dpk_computeconfig_levels"
    And I create a dataset by the name of "model" in the project

  @DAT-65220
  Scenario: DPK with computeConfig on function , module - App should deployed with component config from function
    Given I fetch the dpk from 'apps/app_include_models.json' file
    When I add the context.dataset to the dpk model
    And I set code path "models_flow" to context
    And I pack directory by name "model_flow"
    And I add codebase to dpk
    And I get computeConfig from path "apps/compute_config.json" named "module-level"
    And I add computeConfig to dpk on "modules" component in index "0"
    And I get computeConfig from path "apps/compute_config.json" named "function-level"
    And I add computeConfig to dpk on "functions" component in index "1" on module in index "0"
    And I publish a dpk to the platform
    And  I install the app
    And I set the model in the context
    Then Model object with the same name should be exist
    When i "deploy" the model
    Then i have a model service
    Then I compare service config with context.compute_config_item
    And I uninstall the app
    And I delete model

  @DAT-65109
  Scenario: DPK with computeConfig on function , module and model - App should deployed with component config from model
    Given I fetch the dpk from 'apps/app_include_models.json' file
    When I add the context.dataset to the dpk model
    And I set code path "models_flow" to context
    And I pack directory by name "model_flow"
    And I add codebase to dpk
    And I get computeConfig from path "apps/compute_config.json" named "module-level"
    And I add computeConfig to dpk on "modules" component in index "0"
    And I get computeConfig from path "apps/compute_config.json" named "function-level"
    And I add computeConfig to dpk on "functions" component in index "1" on module in index "0"
    And I get computeConfig from path "apps/compute_config.json" named "deploy-model"
    And I add computeConfig to dpk on "models" component in index "0" with operation "deploy"
    And I publish a dpk to the platform
    And  I install the app
    And I set the model in the context
    Then Model object with the same name should be exist
    When i "deploy" the model
    Then i have a model service
    Then I compare service config with context.compute_config_item