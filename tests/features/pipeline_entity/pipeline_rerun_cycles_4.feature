Feature: Pipeline entity method testing - rerun cycle

  Background: Initiate Platform Interface and create a pipeline
    Given Platform Interface is initialized as dlp and Environment is set according to git branch
    And I create a project by the name of "test_pipeline_rerun_4"
    And I create a dataset with a random name
    When I create a new plain recipe
    And I update dataset recipe to the new recipe
    When I upload the file in path "assets_split/items_upload/0000000162.jpg" with remote name "1.jpg"


  @pipelines.delete
  @DAT-52626
  Scenario: Rerun pipeline - with task node (start-node) should remove item status after rerun
    Given I create pipeline from json in path "pipelines_json/task_dataset_nodes.json"
    And I install pipeline in context
    When I execute pipeline on item
    And I get task by pipeline task node
    And I wait for item to enter task
    And I update item status to "completed" with task id
    Then Cycle completed with save "True"
    When rerun the cycle from the beginning
    And I wait for item status to be "completed" with action "deleted"
    And I update item status to "completed" with task id
    Then Cycle completed with save "False"
    Then the pipeline cycle should be rerun


  @pipelines.delete
  @DAT-52626
  Scenario: Rerun pipeline - with task node (last-node) should remove item status after rerun
    Given I create pipeline from json in path "pipelines_json/dataset_task_nodes.json"
    And I install pipeline in context
    When I execute pipeline on item
    And I get task by pipeline task node
    And I wait for item to enter task
    And I update item status to "completed" with task id
    Then Cycle completed with save "True"
    When rerun the cycle from the "2" node
    And I wait for item status to be "completed" with action "deleted"
    And I update item status to "completed" with task id
    Then Cycle completed with save "False"

