Feature: Test app vars map

  Background: Initialize
    Given Platform Interface is initialized as dlp and Environment is set according to git branch
    And I create a project by the name of "app-vars-map"

  @DAT-80317
  @pipelines.delete
  Scenario: app with map var - Should create pipeline with values
    Given I fetch the dpk from 'apps/dependencies/baseDpkDep.json' file
    When I set code path "models_flow" to context
    And I pack directory by name "model_flow"
    And I add codebase to dpk
    And I publish a dpk to the platform without random name "False"
    When I fetch the dpk from 'apps/app_with_dep_vars.json' file with fix template 'False'
    When I set code path "models_flow" to context
    And I pack directory by name "model_flow"
    And I add codebase to dpk
    And I publish a dpk to the platform
    And I install the app
    And create pipeline from app template
    Then pipeline has ids instead of vars
    And I clean the project