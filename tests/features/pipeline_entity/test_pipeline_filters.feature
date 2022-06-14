Feature: Pipeline resource testing

  Background: Initiate Platform Interface and create a pipeline
    Given Platform Interface is initialized as dlp and Environment is set according to git branch
    And There is a project by the name of "pipeline_resource"
    And I create a dataset with a random name
    When I create a new plain recipe
    And I update dataset recipe to the new recipe

  @pipelines.delete
  @testrail-C4528946
  Scenario: Filter pipeline connector with dataset resource and dataset id values
    When I create filters
    And I add "dataset" filter with "id" and "dataset.id"
    And I create a pipeline with dataset resources
    And I upload item in "0000000162.jpg" to dataset
    Then I expect that pipeline execution has "2" success executions
    And I pause pipeline in context


  @pipelines.delete
  @testrail-C4528946
  Scenario: Filter pipeline connector with dataset resource and random values
    When I create filters
    And I add "dataset" filter with "id" and "123456"
    And I create a pipeline with dataset resources
    And I upload item in "0000000162.jpg" to dataset
    Then I expect that pipeline execution has "1" success executions
    And I pause pipeline in context