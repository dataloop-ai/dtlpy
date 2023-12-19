Feature: Pipeline train node Testing

  Background: Initiate Platform Interface and create a pipeline
    Given Platform Interface is initialized as dlp and Environment is set according to git branch
    And I create a project by the name of "pipeline_train_node"
    And I create a dataset with a random name
    And I upload an item by the name of "test_item.jpg"
    When I upload labels to dataset
    And I upload "5" box annotation to item


  @pipelines.delete
  @DAT-55921
  Scenario: Create pipeline with train node - Execution should success
    When I create a dummy model package by the name of "package-train-node" with entry point "main.py"
    And I create a model from package by the name of "model-train-node" with status "created"
    Given I create pipeline from json in path "pipelines_json/pipeline_train_node.json"
    And I install pipeline in context
    When I execute pipeline with input type "None"
    Then I expect that pipeline execution has "1" success executions

