@rc_only
Feature: Pipeline active learning testing

  Background: Initiate Platform Interface and create a pipeline
    Given Platform Interface is initialized as dlp and Environment is set according to git branch
    And I create a project by the name of "pipeline_active_learning"
    And I create a dataset named "Upload-data"
    And I Add dataset to context.datasets
    When I upload labels to dataset
    Given I create a dataset named "Ground-Truth"
    And I Add dataset to context.datasets
    When I upload labels to dataset

  @pipelines.delete
  @DAT-62553
  Scenario: Create an active learning pipeline flow - Pipeline created from json
    When I validate global app by the name "Active Learning" is installed
    Given I fetch the dpk from 'model_dpk/modelsDpks.json' file
    When I create a dummy model package by the name of "ac-lr-package" with entry point "main.py"
    And I create a model from package by the name of "ac-lr-model" with status "trained" in index "0"
    And I publish a dpk to the platform
    And I install the app
    And i fetch the model by the name "ac-lr-model"
    And I get global dpk by name "active-learning"
    Given I create pipeline from json in path "pipelines_json/active_learning.json"
    When I install pipeline in context
    And I upload items in the path "images_numbers/1_50" to the dataset in index "0"
    And I validate all items is annotated in dataset in index "0"
    And I get task by pipeline task node
    Then I expect "task" created with "50" items
    When I have box annotation_definition with params
      | key    | value    |
      | label  | "Number" |
      | top    | 177      |
      | left   | 172      |
      | bottom | 303      |
      | right  | 322      |
    And I update items annotations in task with context.annotation_definition
    And I update items status to default task actions
    And Dataset in index "1" have "50" items
    When I get last model in project
    Then model metadata should include operation "deploy" with filed "services" and length "1"
    When I execute pipeline with input type "None"
    Then I expect that pipeline execution has "6" success executions
    When I get last model in project
    Then model metadata should include operation "evaluate" with filed "datasets" and length "1"



