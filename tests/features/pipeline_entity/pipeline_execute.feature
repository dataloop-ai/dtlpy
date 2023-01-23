Feature: Pipeline entity method testing

  Background: Initiate Platform Interface and create a pipeline
    Given Platform Interface is initialized as dlp and Environment is set according to git branch
    And I create a project by the name of "test_pipeline_flow"
    And I create a dataset with a random name
    And I upload item in "0000000162.jpg" to dataset
    And I upload item by the name of "test_item.jpg" to a remote path "test"
    And I upload item by the name of "test_item2.jpg" to a remote path "test"
    When I create a new plain recipe
    And I update dataset recipe to the new recipe


  @pipelines.delete
  @testrail-C4533385
  Scenario: pipeline execute batch
    When I create a pipeline with name "test_pipeline_execute"
    And I add a code node to the pipeline
    When I execute the pipeline batch items
    Then pipeline execution are success in "2" items

  @services.delete
  @packages.delete
  @testrail-C4533386
  Scenario: service execute batch
    Given There is a package (pushed from "services/item_with_init") by the name of "services-flow"
    When I deploy a service with init prams
    And I execute the service batch items
    Then service execution are success in "2" items