Feature: Publish multiple models using dpk

  Background:
    Given Platform Interface is initialized as dlp and Environment is set according to git branch
    And I create a project by the name of "multiple_models_dpk"
    And I create a dataset by the name of "model" in the project

  @DAT-52048
  Scenario: Publishing a dpk with multiple models
    Given I fetch the dpk from 'apps/app_include_multiple_models.json' file
    When I add the context.dataset to the dpk model
    And I publish a dpk to the platform
    And  I install the app
    And I add models list to context.models and expect to get "2" models
    Then Model module_name should be "my-adapter-1,my-adapter-2"
    And I uninstall the app
