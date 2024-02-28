Feature: Pipeline evaluate node Testing

  Background: Initiate Platform Interface and create a pipeline
    Given Platform Interface is initialized as dlp and Environment is set according to git branch
    And I create a project by the name of "pipeline_evaluate_node"
    And I create a dataset with a random name
    And I upload an item by the name of "test_item.jpg"
    When I upload labels to dataset
    And I upload "5" box annotation to item

  @pipelines.delete
  @DAT-56168
  Scenario: Create pipeline with evaluate node - Execution should success
    Given I fetch the dpk from 'model_dpk/modelsDpks.json' file
    When I create a dummy model package by the name of "package-evaluate-node" with entry point "main.py"
    And I create a model from package by the name of "model-evaluate-node" with status "trained" in index "0"
    And I publish a dpk to the platform
    And I install the app
    And i fetch the model by the name "model-evaluate-node"
    When i "deploy" the model
    Then model status should be "deployed" with execution "False" that has function "None"
    Given I create pipeline from json in path "pipelines_json/pipeline_evaluate_node.json"
    And I install pipeline in context
    When I execute pipeline with input type "None"
    Then I expect that pipeline execution has "1" success executions
    And I wait "4"
    And Dataset has a scores file