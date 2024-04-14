#Feature: Models create validation
#
#  Background:
#    Given Platform Interface is initialized as dlp and Environment is set according to git branch
#    And I create a project by the name of "model_create_validation"
#    And I create a dataset by the name of "model" in the project
#
#  @DAT-66505
#  Scenario: Install dpk with 2 models with same name - Should failed to install app
#    Given I fetch the dpk from 'model_dpk/modelsDpks.json' file
#    When I create a dummy model package by the name of "dummymodel" with entry point "main.py"
#    And I create a model from package by the name of "test-model" with status "trained" in index "0"
#    And I create a model from package by the name of "test-model" with status "trained" in index "1"
#    And I add the context.dataset to the dpk model
#    And I publish a dpk to the platform
#    And I install the app with exception
#    Then "BadRequest" exception should be raised
#    And "error creating an app , models already exist, Model with this name already exists" in error message
#
