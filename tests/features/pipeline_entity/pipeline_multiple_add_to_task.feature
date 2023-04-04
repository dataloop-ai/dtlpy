Feature: Pipeline entity method testing recomplete items

  Background: Initiate Platform Interface and create a pipeline
    Given Platform Interface is initialized as dlp and Environment is set according to git branch
    And I create a project by the name of "test_pipeline_recomplete"
    And I create a dataset with a random name
    When I create a new plain recipe
    And I update dataset recipe to the new recipe


  @pipelines.delete
  @services.delete
  @DAT-44712
  Scenario: Same item enters a task node twice
    Given a pipeline with same item enters task twice
    When I upload item in "0000000162.jpg" to pipe dataset
    When I execute pipeline on item
    When I wait for item to enter task
    Then I update item status to "complete" with task id
    Then Cycle should be completed
