Feature: Test app umbrella refs - Auto update Pipeline nodes

  Background: Initialize
    Given Platform Interface is initialized as dlp and Environment is set according to git branch
    And I create a project by the name of "auto-update-refs"

  @DAT-72128
  @pipelines.delete
  Scenario: Auto update app with custom node scope node - Should update the node service to latest app version
    Given I publish a pipeline node dpk from file "apps/app_scope_node.json" and with code path "move_item"
    When I install the app
    Given I create pipeline from json in path "pipelines_json/pipeline_scope_node.json"
    And I install pipeline in context
    When I update app auto update to "True"
    And I get the pipeline service
    And I try get the "published_dpk" by id
    Then "service" has app scope
    When I try get the "published_dpk" by id
    And I set code path "update_metadata" to context
    And I pack directory by name "update_metadata"
    And I add codebase to dpk
    And I publish a dpk
    And I wait for app version to be updated according to dpk version
    And I get the pipeline service
    Then "service" has app scope
    And I pause pipeline in context
    And I uninstall the app

  @DAT-72128
  @pipelines.delete
  Scenario: Auto update app with custom node scope node and update pipeline - Should update the node service to latest app version
    Given I publish a pipeline node dpk from file "apps/app_scope_node.json" and with code path "move_item"
    When I install the app
    Given I create pipeline from json in path "pipelines_json/pipeline_scope_node.json"
    When I update pipeline description
    And I install pipeline in context
    When I update app auto update to "True"
    And I get the pipeline service
    And I try get the "published_dpk" by id
    Then "service" has app scope
    When I try get the "published_dpk" by id
    And I set code path "update_metadata" to context
    And I pack directory by name "update_metadata"
    And I add codebase to dpk
    And I publish a dpk
    And I wait for app version to be updated according to dpk version
    And I get the pipeline service
    Then "service" has app scope
    And I pause pipeline in context
    And I uninstall the app

  @DAT-72129
  @pipelines.delete
  Scenario: Auto update app with cloned model nodes - Should update the nodes service to latest app version
    Given I publish a model dpk from file "model_dpk/modelsDpks.json" package "dummymodel" with status "trained"
    When I install the app
    And i fetch the model by the name "test-model"
    And I clone a model and set status "created"
    And I update app auto update to "True"
    Given I create pipeline from json in path "pipelines_json/train_evaluate_nodes.json"
    And I install pipeline in context
    When I get the dpk by name
    And I set code path "model_temp_1" to context
    And I pack directory by name "model_temp_1"
    And I add codebase to dpk
    And I publish a dpk
    And I wait for app version to be updated according to dpk version
    And I get last model in project
    And I execute pipeline with input type "Model"
    And I wait "4"
    And I get service in index "-1"
    Then I validate service response params
      | key             | value |
      | packageRevision | 1.0.1 |
    And "model" has app scope
    And "service" has app scope
    And I pause pipeline in context
    And I uninstall the app

  @DAT-72310
  Scenario: Auto update app with cloned model deploy service - Should update deploy service to latest app version
    Given I publish a model dpk from file "model_dpk/modelsDpks.json" package "dummymodel" with status "trained"
    When I install the app
    And I update app auto update to "True"
    And I get last model in project
    And I clone a model and set status "trained"
    And I "deploy" the model
    And I get the dpk by name
    And I set code path "model_temp_1" to context
    And I pack directory by name "model_temp_1"
    And I add codebase to dpk
    And I publish a dpk
    And I wait for app version to be updated according to dpk version
    And I get last model in project
    And I get service in index "-1"
    Then I validate service response params
      | key             | value |
      | packageRevision | 1.0.1 |
    And "model" has app scope
    And "service" has app scope

