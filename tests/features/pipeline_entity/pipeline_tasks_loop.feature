Feature: Pipeline contex testing

  Background: Initiate Platform Interface and create a pipeline
    Given Platform Interface is initialized as dlp and Environment is set according to git branch
    And I create a project by the name of "test_pipeline_flow"
    And I create a dataset with a random name
    When I create a new plain recipe
    And I update dataset recipe to the new recipe


  @pipelines.delete
  @DAT-81338
  Scenario: pipeline with tasks that has loop - should create all tasks
    Given I create pipeline from json in path "pipelines_json/pipeline_tasks_loop.json"
    And I install pipeline in context
    When I list Tasks by param "project_ids" value "current_project"
    Then I receive a list of "2" tasks