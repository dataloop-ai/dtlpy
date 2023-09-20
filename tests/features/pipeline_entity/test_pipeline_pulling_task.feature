Feature: Pipeline pulling task testing

  Background: Initiate Platform Interface and create a pipeline
    Given Platform Interface is initialized as dlp and Environment is set according to git branch
    And I create a project by the name of "pipeline_resource"
    And I create a dataset with a random name
    When I create a new plain recipe
    And I update dataset recipe to the new recipe


  @pipelines.delete
  @testrail-C4532851
  @DAT-46589
  Scenario: Create pipeline with pulling task - receive the correct task params
    When I create pipeline with pulling task with type "annotation" node and dataset node
      | key                | value |
      | batch_size         | 5     |
      | max_batch_workload | 7     |
      | priority           | LOW   |
    And I get task by pipeline task node
    Then I validate pulling task created equal to pipeline task node


  @pipelines.delete
  @testrail-C4532851
  @DAT-46589
  Scenario: Create pipeline with pulling qa-task - receive the correct qa-task params
    When I create pipeline with pulling task with type "qa" node and dataset node
      | key                | value |
      | batch_size         | 5     |
      | max_batch_workload | 7     |
      | priority           | LOW   |
    And I get task by pipeline task node
    Then I validate pulling task created equal to pipeline task node


  @pipelines.delete
  @testrail-C4532851
  @DAT-46589
  Scenario: Create pipeline with wrong pulling task params - Should rise the correct error
    When I create pipeline with pulling task with type "annotation" node and dataset node
      | key                | value |
      | batch_size         | 10    |
      | max_batch_workload | 7     |
      | priority           | LOW   |
    Then I expect pipeline error to be "Failed to create a task"

  @pipelines.delete
  @testrail-C4532851
  @DAT-46589
  Scenario: Create pipeline with pulling task - receive the correct task params
    When I create pipeline with pulling task with type "annotation" node and dataset node
      | key                | value |
      | batch_size         | 5     |
      | max_batch_workload | 7     |
      | priority           | LOW   |
    And I get task by pipeline task node
    Given There are "10" items
    Then I wait "45"
    When I get Task items by "name"
    Then I receive task items list of "10" items
    And I receive a list of "5" items for each assignment


