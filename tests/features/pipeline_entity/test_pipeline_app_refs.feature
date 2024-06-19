Feature: Test app umbrella refs - Pipeline nodes

  Background: Initialize
    Given Platform Interface is initialized as dlp and Environment is set according to git branch
    And I create a project by the name of "pipeline-refs"

  @DAT-71917
  @pipelines.delete
  Scenario: Update app with custom node scope node - Should update the node service to latest app version
    Given I publish a pipeline node dpk from file "apps/app_scope_node.json" and with code path "move_item"
    When I install the app
    Given I create pipeline from json in path "pipelines_json/pipeline_scope_node.json"
    And I install pipeline in context
    When I get the pipeline service
    And I try get the "published_dpk" by id
    Then "service" has app scope
    When I try get the "published_dpk" by id
    And I set code path "update_metadata" to context
    And I pack directory by name "update_metadata"
    And I add codebase to dpk
    And I publish a dpk
    And I increment app dpk_version
    And I update an app
    And I get the pipeline service
    Then "service" has app scope

  @pipelines.delete
  Scenario: Update app with clone model nodes - Should update the nodes service to latest app version
    Given I publish a model dpk from file "model_dpk/modelsDpks.json" package "dummymodel" with status "trained"
    When I install the app
    And I get the dpk by name
    And I set code path "model_temp_1" to context
    And I pack directory by name "model_temp_1"
    And I add codebase to dpk
    And I publish a dpk
    And I increment app dpk_version
    And I update an app
    And i fetch the model by the name "test-model"
    And I clone a model and set status "created"
    Given I create pipeline from json in path "pipelines_json/train_evaluate_nodes.json"
    And I install pipeline in context
    When I execute pipeline with input type "Model"
    Then I expect that pipeline execution has "2" success executions
    And I wait "4"
    And Dataset has a scores file
