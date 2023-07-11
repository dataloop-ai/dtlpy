Feature: Pipeline resource multiples outputs testing

  Background: Initiate Platform Interface and create a pipeline
    Given Platform Interface is initialized as dlp and Environment is set according to git branch
    And I create a project by the name of "pipeline_limit_many_to_one"
    And I create a dataset with a random name
    When I create a new plain recipe
    And I update dataset recipe to the new recipe


  @pipelines.delete
  @testrail-C4536833
  @DAT-46587
  Scenario: Multiple outputs - Limit many to one - 1000 execution - Cycle status should get success
    Given I create pipeline from json in path "pipelines_json/output_integers_input_integer_1000.json"
    And I install pipeline in context
    When I upload item in "0000000162.jpg" to pipe dataset
    And I execute pipeline with input type "Item"
    Then Pipeline has "1" cycle executions
    And I expect that pipeline execution has "1001" success executions


  @pipelines.delete
  @testrail-C4536833
  @DAT-46587
  Scenario: Multiple outputs - Limit many to one - 1001 execution - Cycle status should get failed
    Given I create pipeline from json in path "pipelines_json/output_integers_input_integer_1001.json"
    And I install pipeline in context
    When I upload item in "0000000162.jpg" to pipe dataset
    And I execute pipeline with input type "Item"
    When I get pipeline execution in index "0"
    Then Pipeline has "1" cycle executions
    And I validate Cycle execution status is "failed"

