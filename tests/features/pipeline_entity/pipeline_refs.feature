Feature: Test pipeline refs

  Background: Initiate Platform Interface and create a project
    Given Platform Interface is initialized as dlp and Environment is set according to git branch
    And I create a project by the name of "pipeline-refs"

  @DAT-64799
  @DAT-71435
  Scenario: Test full pipeline refs + cleanup
    When get global model package
    And I create a model with a random name
    Given model is trained
    And a service
    And a dpk with custom node
    And an app
    And pipeline with model, service, code and custom nodes
    When I install pipeline
    Then service should have pipeline refs and cannot be uninstall
    And model should have pipeline refs and cannot be deleted
    And code node package should have pipeline refs
    And code node service should have pipeline refs and cannot be uninstall
    And app should have pipeline refs and cannot be uninstall
    When I delete pipeline
    Then service should not have pipeline refs and uninstall service "True"
    And model should not have pipeline refs and delete model "True"
    And app should not have pipeline refs and uninstall app "True"

  @DAT-70831
  @pipelines.delete
  Scenario: Pipeline refs of services created in pipeline runtime
    Given I create a dataset with a random name
    When I upload labels to dataset
    Given I fetch the dpk from 'model_dpk/modelsDpks.json' file
    When I create a dummy model package by the name of "dummymodel" with entry point "main.py"
    And I create a model from package by the name of "test-model-trained" with status "trained" in index "0"
    And I create a model from package by the name of "test-model-created" with status "created" in index "1"
    And I publish a dpk to the platform
    And I install the app
    Given I have a pipeline with train node and evaluate node
    When I install pipeline
    When I execute pipeline without input
    Given I pause pipeline when executions are created
    When I install pipeline
    Then model services should still have refs


  @DAT-81446
  @pipelines.delete
  Scenario: Updating pipeline servie out of scope - service should update as expected
    Given I create pipeline with the name "pipeline"
    And I create "code" node with params
      | key      | value |
      | position | (1,1) |
    When I add and connect all nodes in list to pipeline entity
    And I install pipeline in context
    And I get service in index "-1"
    When I pause service in context
    And I pause pipeline in context
    When I update pipeline
    Then service status is "Paused"
    When I install pipeline in context
    Then service status is "Active"