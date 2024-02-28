Feature: Pipeline entity method testing - rerun cycle

  Background: Initiate Platform Interface and create a pipeline
    Given Platform Interface is initialized as dlp and Environment is set according to git branch
    And I create a project by the name of "pipeline_validation"


  @pipelines.delete
  @DAT-54410
  Scenario: Pipeline validation - Input output resource missmatch - Should failed to update
    Given I create pipeline with the name "input-output"
    And I create "code" node with params
      | key      | value |
      | position | (1,1) |
    And I create "code" node with params
      | key                | value   |
      | position           | (2,2)   |
      | input_type         | Dataset |
      | input_name         | dataset |
      | input_display_name | dataset |
    When I add and connect all nodes in list to pipeline entity
    Then I receive error with status code "400"
    And "Invalid input specified, Failed to update pipeline: connection source and target ports must be of the same type" in error message


  @pipelines.delete
  @DAT-54411
  Scenario: Pipeline validation - Output without action - port with action - Should failed to update
    Given I create pipeline with the name "output-action"
    And I create "code" node with params
      | key      | value |
      | position | (1,1) |
    And I create "code" node with params
      | key      | value |
      | position | (2,2) |
    When I add and connect all nodes in list to pipeline entity
    And I add action "test" to connection in index "0"
    Then I receive error with status code "400"
    And "Invalid input specified, Cannot read properties of undefined (reading 'includes')" in error message

  @pipelines.delete
  @DAT-54412
  Scenario: Pipeline validation - Try to add another start node - Should failed to update
    Given I create pipeline with the name "multiple-start"
    And I create "code" node with params
      | key      | value |
      | position | (1,1) |
    And I create "code" node with params
      | key      | value |
      | position | (2,2) |
    When I add all nodes in list to pipeline entity
    When I update node in index "1" to start node
    Then I receive error with status code "400"
    And "Invalid input specified, Pipeline may only include 1 root node" in error message


  @pipelines.delete
  @DAT-54772
  Scenario: Pipeline validation - At least one node with wrong validation - Should failed to install
    Given I create pipeline with the name "at-least-one"
    And I create a dataset with a random name
    When I create a new plain recipe
    And I update dataset recipe to the new recipe
    Given I create "dataset" node with params
      | key      | value |
      | position | (1,1) |
    And I create "task" node with params
      | key      | value |
      | position | (2,2) |
    And I create "dataset" node with params
      | key      | value |
      | position | (3,3) |
    When I update pipeline context.node "dataset_id" with "None"
    And I add and connect all nodes in list to pipeline entity
    And I try to install pipeline in context
    Then I receive error with status code "400"
    And "must have a datasetId" in error message