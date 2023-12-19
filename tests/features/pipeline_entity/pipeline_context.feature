@bot.create
Feature: Pipeline contex testing

  Background: Initiate Platform Interface and create a pipeline
    Given Platform Interface is initialized as dlp and Environment is set according to git branch
    And I create a project by the name of "test_pipeline_flow"
    And I create a dataset with a random name
    When I create a new plain recipe
    And I update dataset recipe to the new recipe


  @pipelines.delete
  @DAT-45831
  Scenario: pipeline with context
    Given I have a custom "context" pipeline from json
    When I upload item in "0000000162.jpg" to pipe dataset
    And I wait for item to enter task
    And I update item status to "completed" with task id
    Then Context should have all required properties


  @pipelines.delete
  @services.delete
  @packages.delete
  @DAT-56555
  Scenario: Faas and Code node with trigger Item_status - Should get correct pipeline.context
    Given There is a package (pushed from "pipeline_faas_services/context") by the name of "node-context"
    When I deploy a service
      | service_name=node-context | package=node-context | revision=None | config=None | runtime=None |
    Given I create pipeline from json in path "pipelines_json/pipeline_context_trigger_item_status.json"
    And I install pipeline in context
    When I upload item in "0000000162.jpg" to pipe dataset
    And I get task by pipeline task node
    And I wait for item to enter task
    And I update item status to "completed" with task id
    Then Context should have all required properties