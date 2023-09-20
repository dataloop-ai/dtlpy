Feature: Pipeline entity method testing - Task node execution

  Background: Initiate Platform Interface and create a pipeline
    Given Platform Interface is initialized as dlp and Environment is set according to git branch
    And I create a project by the name of "pipeline_task_execute_twice"
    And I create a dataset with a random name
    When I create a new plain recipe
    And I update dataset recipe to the new recipe
    When I upload the file in path "assets_split/items_upload/0000000162.jpg" with remote name "1.jpg"


  @pipelines.delete
  @DAT-52654
  Scenario: Execute task node twice with the same item - Should remove the assignment status
    Given I create pipeline with the name "pipeline"
    And I create "task" node with params
      | key      | value |
      | position | (1,1) |
    When I add and connect all nodes in list to pipeline entity
    And I install pipeline in context
    When I execute pipeline on item
    And I get task by pipeline task node
    And I wait for item to enter task
    And I update item status to "complete" with task id
    And I execute pipeline on item
    Then I wait for item status to be "complete" with action "deleted"