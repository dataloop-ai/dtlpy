Feature: Pipeline create method testing

  Background: Initiate Platform Interface and create a pipeline
    Given Platform Interface is initialized as dlp and Environment is set according to git branch
    And I create a project by the name of "node_action_empty_list"
    And I create a dataset with a random name


  @pipelines.delete
  @DAT-90031
  Scenario: Create pipeline with action only in connection - Should Failed to create pipeline
    Given I create pipeline from json in path "pipelines_json/connection_action.json"
    Then I receive error with status code "400"
    And "Invalid input specified, Failed to create pipeline: connection action do not includes in port actions" in error message

  @pipelines.delete
  @DAT-90031
  Scenario: Create pipeline with node output empty list action connection and run pipeline - Cycle should success
    Given I create pipeline from json in path "pipelines_json/output_action_empty_list.json"
    And I install pipeline in context
    When I upload item in "0000000162.jpg" to pipe dataset
    And I execute pipeline with input type "Item"
    Then Pipeline has "1" cycle executions
    And I expect that pipeline execution has "2" success executions

