Feature: Test pipeline model genai

  Background: Initialize
    Given Platform Interface is initialized as dlp and Environment is set according to git branch
    And I create a project by the name of "pipeline-gen-model"


  @DAT-75203
  @pipelines.delete
  Scenario: Create pipeline with gen model
    Given I publish a model dpk from file "model_dpk/basicModelDpkGen.json" package "dummymodel" with status "trained"
    When I install the app without custom_installation
    And I get last model in project
    And "model" has app scope
    And model should be with mltype "LLM"
    And I create a pipeline with gen ai model
    And i update pipeline model node in index "0" configration
    Then model should have a new configration
    When I install pipeline in context
    And I upload item in "0000000162.jpg"
    And I execute pipeline with input type "Item"
    Then Pipeline has "1" cycle executions
    And I expect that pipeline execution has "1" success executions



