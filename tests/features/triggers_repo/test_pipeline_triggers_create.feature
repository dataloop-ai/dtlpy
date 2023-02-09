Feature: Pipeline entity DatasetNode triggers method testing

  Background: Initiate Platform Interface and create a pipeline
    Given Platform Interface is initialized as dlp and Environment is set according to git branch
    And I create a project by the name of "test_pipeline_datasetNode"
    And I create a dataset with a random name
    And I add folder "pipeline" to context.dataset

  @pipelines.delete
  @testrail-C4533426
  Scenario: Create pipeline with dataset node > Should build trigger with default and custom filter - Executions should success
    When I create a pipeline with 2 dataset nodes and trigger with filters
      | key                      | value   |
      | metadata.system.mimetype | *image* |
    Then pipeline trigger created with filter params
      | datasetId, dir, metadata.system.mimetype |
    When I upload file in path "0000000162.jpg" to remote path "/pipeline"
    Then I expect that pipeline execution has "2" success executions
    When I get all items
    Then I receive a list of "2" items