Feature: Pipeline resource connectors testing

  Background: Initiate Platform Interface and create a pipeline
    Given Platform Interface is initialized as dlp and Environment is set according to git branch
    And I create a project by the name of "pipeline_connectors"
    And I create a dataset with a random name
    When I create a new plain recipe
    And I update dataset recipe to the new recipe

  @pipelines.delete
  @testrail-C4533573
  @DAT-46585
  @DAT-52903
  Scenario: Code node with 2 outputs - Should pass the output to correct input
    When I create a pipeline with code nodes with 2 outputs and code node with 2 inputs
    And I upload item in "0000000162.jpg" to dataset
    Then I expect that pipeline execution has "2" success executions
    And I pause pipeline in context

  @pipelines.delete
  @DAT-97125
  Scenario: Pipeline connector with regex filter - Should move the correct item (positive)
    Given I create pipeline from json in path "pipelines_json/pipeline_connector_regex_filter.json" no error
    And I upload item in "0000000162.jpg" to dataset
    When I update item metadata with '{"user": {"exif": {"Make": "Canon12345"}}}'
    And I install pipeline in context
    And I execute the pipeline on item
    Then I expect that pipeline execution has "2" success executions
    And I pause pipeline in context

  @pipelines.delete
  @DAT-97414
  Scenario: Pipeline connector with regex filter - Should not move the item (negative)
    Given I create pipeline from json in path "pipelines_json/pipeline_connector_regex_filter.json" no error
    And I upload item in "0000000162.jpg" to dataset
    When I update item metadata with '{"user": {"exif": {"Make": "test"}}}'
    And I install pipeline in context
    And I execute the pipeline on item
    Then I expect that pipeline execution has "1" success executions
    And I pause pipeline in context
