Feature: Pipeline update testing

  Background: Initiate Platform Interface and create a pipeline
    Given Platform Interface is initialized as dlp and Environment is set according to git branch
    And There is a project by the name of "test_pipeline_flow"
    And I create a dataset with a random name
    When I create a new plain recipe
    And I update dataset recipe to the new recipe

  @pipelines.delete
  Scenario: Update pipeline
    When I create a package and service to pipeline
    And I create a pipeline from json
    And I update pipeline description
    Then Pipeline received equals Pipeline changed except for "description"
