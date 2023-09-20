Feature: Pipeline entity method testing - rerun cycle

  Background: Initiate Platform Interface and create a pipeline
    Given Platform Interface is initialized as dlp and Environment is set according to git branch
    And I create a project by the name of "test_pipeline_rerun_3"
    And I create a dataset with a random name
    When I create a new plain recipe
    And I update dataset recipe to the new recipe
    When I upload the file in path "assets_split/items_upload/0000000162.jpg" with remote name "1.jpg"


  @pipelines.delete
  @DAT-52397
  Scenario: Rerun pipeline with multiple inputs - Should have input cache
    Given I create pipeline from json in path "pipelines_json/rerun_multiple_inputs.json"
    And I install pipeline in context
    When I execute pipeline on item
    Then Cycle completed with save "True"
    When rerun the cycle from the "3" node
    Then Cycle completed with save "False"
    Then the pipeline cycle should be rerun

