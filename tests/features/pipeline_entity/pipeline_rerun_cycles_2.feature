@DAT-49332
Feature: Pipeline entity method testing - rerun cycle

  Background: Initiate Platform Interface and create a pipeline
    Given Platform Interface is initialized as dlp and Environment is set according to git branch
    And I create a project by the name of "test_pipeline_rerun"
    And I create a dataset with a random name
    When I create a new plain recipe
    And I update dataset recipe to the new recipe
    When I upload the file in path "assets_split/items_upload/0000000162.jpg" with remote name "1.jpg"
    When I build a pipeline with dynamic node status


  @pipelines.delete
  Scenario: rerun pipeline cycle from the beginning root case
    When rerun the cycle from the beginning
    When I execute pipeline on item
    Then Cycle completed with save "True"
    When rerun the cycle from the beginning
    Then Cycle completed with save "False"
    Then the pipeline cycle should be rerun


  @pipelines.delete
  Scenario: rerun pipeline cycle from the beginning trigger case
    When I upload the file in path "assets_split/items_upload/0000000162.jpg" with remote name "2.jpg"
    Then Cycle completed with save "True"
    When rerun the cycle from the beginning
    Then Cycle completed with save "False"
    Then the pipeline cycle should be rerun


  @pipelines.delete
  Scenario: rerun pipeline Execution
    When I execute pipeline on item
    Then Cycle completed with save "True"
    When rerun the cycle from the "2" node
    Then Cycle completed with save "False"
    Then the pipeline cycle should be rerun

  @pipelines.delete
  Scenario: rerun pipeline Execution from the failed node
    When I execute pipeline on item
    Then Cycle completed with save "True"
    When rerun the cycle from the failed node
    And I wait "20"
    Then Cycle completed with save "False"
    Then the pipeline cycle should be rerun
    Then Cycle completed with save "True"
    When rerun the cycle from the failed node
    Then the pipeline cycle should not change
