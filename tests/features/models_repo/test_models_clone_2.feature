Feature: Models repository clone testing 2

  Background: Initiate Platform Interface and create a project
    Given Platform Interface is initialized as dlp and Environment is set according to git branch
    And I create a project by the name of "model_configuration"
    And I create a dataset by the name of "model" in the project
    When I upload labels to dataset

  @DAT-65220
  Scenario: Clone model with custom configuration - Should clone also the configuration
    Given I fetch the dpk from 'apps/app_include_models.json' file
    When I add the context.dataset to the dpk model
    And I set code path "models_flow" to context
    And I pack directory by name "model_flow"
    And I add codebase to dpk
    And I get computeConfig from path "apps/compute_config.json" named "module-level"
    And I add computeConfig to dpk on "modules" component in index "0"
    And I get computeConfig from path "apps/compute_config.json" named "function-level"
    And I add computeConfig to dpk on "functions" component in index "2" on module in index "0"
    And I publish a dpk to the platform
    And  I install the app
    And I set the model in the context
    When i clone a model
    Then Model object with the same name should be exist
    When i "train" the model
    Then i have a model service
    Then I compare service config with context.compute_config_item