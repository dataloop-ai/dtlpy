Feature: Pipeline entity method testing

  Background: Initiate Platform Interface and create a pipeline
    Given Platform Interface is initialized as dlp and Environment is set according to git branch
    And I create a project by the name of "test_pipeline_flow"
    And I create a dataset with a random name
    When I create a new plain recipe
    And I update dataset recipe to the new recipe


  @pipelines.delete
  @testrail-C4532486
  @DAT-46581
  Scenario: pipeline flow
    When I create a package and service to pipeline
    And I create a pipeline from sdk
    And I add a node and connect it to the start node
    Then New node is the start node

  @pipelines.delete
  @DAT-79613
  Scenario: Cron trigger on regular node (not start node)
    Given pipeline with 2 nodes
    And the node which is not the start node has a cron trigger
    When installing the pipeline
    Then the relevant node should be executed

