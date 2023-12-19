Feature: Pipeline update testing

  Background: Initiate Platform Interface and create a pipeline
    Given Platform Interface is initialized as dlp and Environment is set according to git branch
    And I create a project by the name of "test_pipeline_update"
    And I create a dataset with a random name
    When I create a new plain recipe
    And I update dataset recipe to the new recipe

  @pipelines.delete
  @testrail-C4523145
  @DAT-46582
  Scenario: Update pipeline with description
    Given I create pipeline with the name "pipeline"
    And I create "dataset" node with params
      | key      | value |
      | position | (1,1) |
    And I create "dataset" node with params
      | key      | value |
      | position | (2,2) |
    When I add and connect all nodes in list to pipeline entity
    And I install pipeline in context
    And I update pipeline description
    Then Pipeline received equals Pipeline changed except for "description"
    Then "update_pipeline" has updatedBy field


  @pipelines.delete
  @DAT-52687
  Scenario: Try to update pipeline with dataset node input output loop - Should failed to update
    Given I create pipeline with the name "pipeline"
    And I create "dataset" node with params
      | key      | value |
      | position | (1,1) |
    When I update node input output to infinite loop
    Then "Failed to update pipeline: Infinite Loop detected for node "random_dataset" in error message

  @pipelines.delete
  @DAT-52687
  Scenario: Try to update pipeline with node input output loop - Should failed to update
    Given I create pipeline with the name "pipeline"
    And I create "code" node with params
      | key      | value |
      | position | (1,1) |
    When I update node input output to infinite loop
    Then "Failed to update pipeline: Infinite Loop detected for node "codenode" in error message


  @pipelines.delete
  @DAT-52687
  Scenario: Try to create pipeline with code node input output loop - Should failed to update
    Given I create pipeline from json in path "pipelines_json/infinite_loop.json"
    Then "Failed to create pipeline: Infinite Loop detected for node "random_dataset" in error message