Feature: Test pipeline models compute configs

  Background: Initiate Platform Interface and create a project
    Given Platform Interface is initialized as dlp and Environment is set according to git branch
    And I create a project by the name of "pipeline-compute-configs"


  @DAT-66085
  Scenario: Test pipeline models compute configs - base case
    Given a dpk with models and compute configs
    And an app
    And pipeline with train model
    And models are set in context
    When I install pipeline
    And I execute pipeline on model with compute configs
    Then service should use model train compute config
    When I execute pipeline on model with config in module
    Then service should use model module compute config
    When I execute pipeline on model with config in function
    Then service should use model function compute config
