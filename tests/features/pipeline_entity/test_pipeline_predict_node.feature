Feature: Pipeline predict node Testing

  Background: Initiate Platform Interface and create a pipeline
    Given Platform Interface is initialized as dlp and Environment is set according to git branch
    And I create a project by the name of "pipeline_predict_node"
    And I create a dataset with a random name
    When I upload labels to dataset

  @pipelines.delete
  @DAT-56147
  Scenario: Create pipeline with predict node - Execution should success
    When I create a dummy model package by the name of "package-predict-node" with entry point "main.py"
    And I create a model from package by the name of "model-predict-node" with status "trained"
    Given I create pipeline from json in path "pipelines_json/pipeline_predict_node.json"
    And I install pipeline in context
    And Item in path "0000000162.jpg" is uploaded to "Dataset"
    When I execute pipeline on item
    Then I expect that pipeline execution has "1" success executions
    And I validate item is annotated
