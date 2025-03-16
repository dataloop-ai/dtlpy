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
      | key      | value          |
      | position | (1,1)          |
      | name     | Task DAT-52654 |
    When I add and connect all nodes in list to pipeline entity
    And I install pipeline in context
    When I execute pipeline on item
    And I get task by pipeline task node
    And I wait for item to enter task
    And I update item status to "complete" with task id
    And I execute pipeline on item
    Then I wait for item status to be "complete" with action "deleted"


  @pipelines.delete
  @DAT-63245
  Scenario: Create task node with item and delete node shouldn't delete task
    Given I create pipeline with the name "pipeline"
    And I create "task" node with params
      | key      | value          |
      | position | (1,1)          |
      | name     | Task DAT-63245 |
    When I add and connect all nodes in list to pipeline entity
    And I install pipeline in context
    And I execute pipeline on item
    And I get task by pipeline task node
    And I wait for item to enter task
    And I pause pipeline in context
    And I delete all nodes
    And I wait "8"
    Then I get task by pipeline task node


  @DAT-73857
  @pipelines.delete
  Scenario: Pipeline with many to one task node
    Given I create a dataset with a random name
    When I upload the file in path "assets_split/items_upload/0000000162.jpg" with remote name "1.jpg"
    When I upload the file in path "assets_split/items_upload/0000000162.jpg" with remote name "2.jpg"
    When I upload the file in path "assets_split/items_upload/0000000162.jpg" with remote name "3.jpg"
    When I upload the file in path "assets_split/items_upload/0000000162.jpg" with remote name "4.jpg"
    When I upload the file in path "assets_split/items_upload/0000000162.jpg" with remote name "5.jpg"
    Given a pipeline with task node that receives many to one input
    Given I install pipeline in context
    Given I execute the pipeline on item
    When I set status on some of the input items
    Then cycle should be inProgress and task node should be inProgress
    When I set status on all input items
    Then cycle should be completed and task node should be completed