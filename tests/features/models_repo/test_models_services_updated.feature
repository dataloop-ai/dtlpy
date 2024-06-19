Feature: Test app umbrella - Update app should add app refs

  Background:
    Given Platform Interface is initialized as dlp and Environment is set according to git branch
    And I create a project by the name of "model_service_updated"


  @DAT-71922
  Scenario: Update app with model train service - Should create train service with latest app version
    Given I publish a model dpk from file "model_dpk/modelsDpks.json" package "dummymodel" with status "created"
    When I install the app
    And I get the dpk by name
    And I set code path "model_temp_1" to context
    And I pack directory by name "model_temp_1"
    And I add codebase to dpk
    And I publish a dpk
    And I increment app dpk_version
    And I update an app
    And i fetch the model by the name "test-model"
    And I "train" the model
    And I get service from context.execution
    Then I validate service response params
      | key             | value |
      | packageRevision | 1.0.1 |
    And "model" has app scope
    And "service" has app scope

  @DAT-71923
  @services.delete
  Scenario: Update app with model evaluate service - Should create evaluate service with latest app version
    Given I publish a model dpk from file "model_dpk/modelsDpks.json" package "dummymodel" with status "trained"
    When I install the app
    And I get the dpk by name
    And I set code path "model_temp_1" to context
    And I pack directory by name "model_temp_1"
    And I add codebase to dpk
    And I publish a dpk
    And I increment app dpk_version
    And I update an app
    And I get last model in project
    And I "evaluate" the model
    And I get service from context.execution
    Then I validate service response params
      | key             | value |
      | packageRevision | 1.0.1 |
    And "model" has app scope
    And "service" has app scope


  @DAT-71993
  Scenario: Update app with cloned model deploy service - Should update deploy service to latest app version
    Given I publish a model dpk from file "model_dpk/modelsDpks.json" package "dummymodel" with status "trained"
    When I install the app
    And I get last model in project
    And I clone a model and set status "trained"
    And I "deploy" the model
    And I get the dpk by name
    And I set code path "model_temp_1" to context
    And I pack directory by name "model_temp_1"
    And I add codebase to dpk
    And I publish a dpk
    And I increment app dpk_version
    And I update an app
    And I get last model in project
    Then I validate service response params
      | key             | value |
      | packageRevision | 1.0.1 |
    And "model" has app scope


  @DAT-71997
  Scenario: Update app with cloned model train service - Should create train service with latest app version
    Given I publish a model dpk from file "model_dpk/modelsDpks.json" package "dummymodel" with status "created"
    When I install the app
    And I get last model in project
    And I clone a model
    And I get the dpk by name
    And I set code path "model_temp_1" to context
    And I pack directory by name "model_temp_1"
    And I add codebase to dpk
    And I publish a dpk
    And I increment app dpk_version
    And I update an app
    And I get last model in project
    And I "train" the model
    And I get service from context.execution
    Then I validate service response params
      | key             | value |
      | packageRevision | 1.0.1 |
    And "model" has app scope
    And "service" has app scope