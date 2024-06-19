Feature: Pipeline service uninstall

  Background: Initiate Platform Interface
    Given Platform Interface is initialized as dlp and Environment is set according to git branch
    And I create a project by the name of "test_pipeline_flow"
    And I create a dataset with a random name
    And I upload item by the name of "test_item.jpg" to a remote path "test"
    When I create a new plain recipe
    And I update dataset recipe to the new recipe


  @DAT-56574
  @pipelines.delete
  Scenario: pipeline execute batch
    When I create a pipeline with name "test_pipeline_1"
    And I add a code node to the pipeline
    And I install pipeline
    And I pause service
    And I execute the pipeline batch items
    And I try to uninstall service
    Then "Unable to delete service" in error message
    When I terminate an execution
    And I pause pipeline in context
    And I uninstall service