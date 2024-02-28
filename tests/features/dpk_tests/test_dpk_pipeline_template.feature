@rc_only
Feature: DPK Pipeline template testing

  Background: Initiate Platform Interface and create a pipeline
    Given Platform Interface is initialized as dlp and Environment is set according to git branch
    And I create a project by the name of "pipeline_active_learning"
    And I create a dataset named "Upload-data"
    And I Add dataset to context.datasets
    And I create a dataset named "Ground-Truth"
    And I Add dataset to context.datasets

  @pipelines.delete
  @DAT-64404
  Scenario: Create an active learning pipeline template from dpk  - Should install the app
    When I validate global app by the name "Active Learning" is installed
    Given I fetch the dpk from 'model_dpk/modelsDpks.json' file
    When I create a dummy model package by the name of "ac-lr-package" with entry point "main.py"
    And I create a model from package by the name of "ac-lr-model" with status "trained" in index "0"
    When I get global dpk by name "active-learning"
    Given I fetch the dpk from 'apps/active_learning_template_pipe.json' file
    When I publish a dpk to the platform
    And I install the app




