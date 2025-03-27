@ATP @AIRGAPPED
Feature: Active Learning Pipeline testing

  Background: Initiate Platform Interface and create a pipeline
    Given Platform Interface is initialized as dlp and Environment is set according to git branch
    And I create a project by the name of "pipeline_active_learning_flow"
    Given I create a dataset named "Upload-data"
    And I Add dataset to context.datasets
    When I upload labels to dataset
    Given I create a dataset named "Ground-Truth"
    And I Add dataset to context.datasets
    When I upload labels to dataset

  @pipelines.delete
  @DAT-79537
  Scenario: Active learning pipeline flow
    When I validate global app by the name "Active Learning" is installed
    """
    ##   Steps for global pipeline app
    #    Given I fetch the dpk from 'apps/active_learning_offline.json' file
    #    When I publish a dpk to the platform
    #    And I install the app
    #    And I save "published_dpk" in context.saved_dpk
    #    Then I validate no error in context
    """
    When I list a project pipelines i get "0"
    Given I fetch the dpk from 'model_dpk/FlowModelsDpks.json' file
    When I create a dummy model package by the name of "ac-lr-package" with entry point "main.py"
    And I create a model from package by the name of "ac-lr-model" with status "trained" in index "0" "without" artifacts
    And I publish a dpk to the platform
    And I install the app
    And i fetch the model by the name "ac-lr-model"
    When I get global dpk by name "active-learning"
    """
    ##   Steps for global pipeline app
    #    When I try get the "saved_dpk" by name
    #    Then I validate no error in context
    """
    Given I create pipeline from json in path "pipelines_json/active_learning_flow.json"
    Then I validate no error in context
    When I list a project pipelines i get "1"
    And I update pipeline variables with the params
      | variable-name        | value          |
      | Raw Dataset          | datasets[0].id |
      | Ground Truth Dataset | datasets[1].id |
      | Best Model           | model.id       |
    When I install pipeline
    """
    ##   Steps for global pipeline app
    #    When I try to update install pipeline
    #    Then "installed" in error message with status code "400"
    """
    Then Services are created with expected configuration
    Then I have "2" triggers in project
    When I upload items in the path "images_numbers/1_50" to the dataset in index "0"
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
    And I update items status to default task actions with task id
    When I get qa task by pipeline qa task node
    Then I expect "qa_task" created with "50" items
    When I update items status to default qa_task actions with qa_task id
    And Dataset in index "1" have "50" items
    When I execute pipeline using cron trigger for node "Create New Model"
    Then I expect that pipeline execution has "6" success executions - ALP "True"
    When I get last model in project
    Then model metadata should include operation "deploy" with filed "services" and length "1"
    When I get node by name "Update Variables"
    And I execute node by node id "context.node.node_id"
    Then I expect that pipeline execution has "1" success executions

