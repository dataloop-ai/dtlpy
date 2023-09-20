Feature: Pipeline resource connectors testing

  Background: Initiate Platform Interface and create a pipeline
    Given Platform Interface is initialized as dlp and Environment is set according to git branch
    And I create a project by the name of "pipeline_connectors"
    And I create a dataset with a random name
    When I create a new plain recipe
    And I update dataset recipe to the new recipe

  @pipelines.delete
  @testrail-C4533573
  @DAT-46585
  @DAT-52903
  Scenario: Code node with 2 outputs - Should pass the output to correct input
    When I create a pipeline with code nodes with 2 outputs and code node with 2 inputs
    And I upload item in "0000000162.jpg" to dataset
    Then I expect that pipeline execution has "2" success executions
    And I pause pipeline in context
