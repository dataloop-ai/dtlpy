Feature: Test app umbrella refs - Pipeline nodes

  Background: Initialize
    Given Platform Interface is initialized as dlp and Environment is set according to git branch
    And I create a project by the name of "pipeline-refs"

  @DAT-84467
  @pipelines.delete
  Scenario: Update app with custom node scope node - Should update the node service to latest app version
    Given I publish a model dpk from file "model_dpk/modelsDpks.json" package "dummymodel" with status "trained"
    When I install the app
    And i fetch the model by the name "test-model"
    Given I publish a pipeline node dpk from file "apps/app_scope_node.json" and with code path "move_item"
    When I install the app
    Given I create pipeline from json in path "pipelines_json/pipeline_scope_node.json"
    When I add a code node to the pipeline
    And I add a predict node to the pipeline
    And i update runnerImage "python:3.10" to pipeline node with type "code"
    And i update runnerImage "python:3.10" to pipeline node with type "custom"
    And i update runnerImage "python:3.10" to pipeline node with type "ml"
    And I install pipeline in context
    And i get the service for the pipeline node with type "code"
    Then service runnerImage is "python:3.10"
    When i get the service for the pipeline node with type "custom"
    Then service runnerImage is "python:3.10"
    When i get the service for the pipeline node with type "ml"
    Then service runnerImage is "python:3.10"
    When i update runnerImage "python:3.11" to pipeline node with type "code"
    And i get the service for the pipeline node with type "code"
    Then service runnerImage is "python:3.11"
    When i update runnerImage "python:3.11" to pipeline node with type "custom"
    And i get the service for the pipeline node with type "custom"
    Then service runnerImage is "python:3.11"
    When i update runnerImage "python:3.11" to pipeline node with type "ml"
    And i get the service for the pipeline node with type "ml"
    Then service runnerImage is "python:3.11"