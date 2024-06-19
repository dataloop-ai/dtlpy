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
  @testrail-C4536833
  @DAT-70139
  Scenario: Multiple outputs - rerun cycle
    Given I create pipeline from json in path "pipelines_json/output_integers_input_integer_1000.json"
    And I install pipeline in context
    When I upload item in "0000000162.jpg" to pipe dataset
    And I execute pipeline with input type "Item"
    Then Pipeline has "1" cycle executions
    And I expect that pipeline execution has "1001" success executions
    When rerun the cycle from the beginning
    And I wait "20"
    Then Cycle completed with save "False"
    Then the pipeline cycle should be rerun

  @pipelines.delete
  @DAT-70139
  Scenario: rerun pipeline cycle from the beginning root case
    When I execute pipeline on item
    Then Cycle completed with save "True"
    When rerun the cycle from the beginning
    Then Cycle completed with save "True"
    When rerun the cycle from the beginning
    Then Cycle completed with save "False"
    Then the pipeline cycle should be rerun

#  @pipelines.delete
#  Scenario: rerun pipeline cycle from the beginning task
#    When I create a package and service to pipeline
#    And I create a pipeline from sdk
#    And I upload item in "0000000162.jpg" to pipe dataset
#    Then verify pipeline flow result
#    When rerun the cycle from the beginning
#    And I wait "20"
#    Then the pipeline cycle should be rerun
#    And Cycle status should be "in-progress"


  @pipelines.delete
  @DAT-70139
  Scenario: rerun pipeline cycle from executions
    When I execute pipeline on item
    Then Cycle completed with save "True"
    When rerun the cycle from the execution
    Then Cycle completed with save "False"
    Then the pipeline cycle should be rerun