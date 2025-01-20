Feature: Models repository train function testing

  Background: Initiate Platform Interface and create a project
    Given Platform Interface is initialized as dlp and Environment is set according to git branch
    And I create a project by the name of "model-train"
    And I create a dataset with a random name
    And I upload an item by the name of "test_item.jpg"
    When I upload labels to dataset
    And I upload "5" box annotation to item

  @DAT-68045
  @DAT-69061
  Scenario: Train model without mandatory params - Should return correct errors
    Given I fetch the dpk from 'model_dpk/modelsDpks.json' file
    When I create a dummy model package by the name of "dummymodel" with entry point "main.py"
    And I create a model from package by the name of "test-model" with status "created" in index "0"
    And I remove attributes "datasetId,labels" from dpk model in index "0"
    Given I publish a dpk to the platform
    When dpk has base id
    And i save dpk base id
    And I install the app
    And i fetch the model by the name "test-model"
    Then "model" has app scope
    When I "train" the model with exception "True"
    Then "Must provide a dataset to train model" in error message
    And I clean the project

  @DAT-68045
  @DAT-69061
  Scenario: Train model without mandatory params - Should return correct errors
    Given I fetch the dpk from 'model_dpk/modelsDpks.json' file
    When I create a dummy model package by the name of "dummymodel" with entry point "main.py"
    And I create a model from package by the name of "test-model" with status "created" in index "0"
    And I remove attributes "labels" from dpk model in index "0"
    Given I publish a dpk to the platform
    When dpk has base id
    And i save dpk base id
    And I install the app
    And i fetch the model by the name "test-model"
    Then "model" has app scope
    When I "train" the model with exception "True"
    Then "Must provide labels to train model" in error message
    And I clean the project


  @DAT-68045
  @DAT-69061
  Scenario: Train model without mandatory params - Should return correct errors
    Given I fetch the dpk from 'model_dpk/modelsDpks.json' file
    When I create a dummy model package by the name of "dummymodel" with entry point "main.py"
    And I create a model from package by the name of "test-model" with status "created" in index "0"
    Given I publish a dpk to the platform
    When dpk has base id
    And i save dpk base id
    And I install the app
    And i fetch the model by the name "test-model"
    Then "model" has app scope
    When I "train" the model with exception "True"
    And I "train" the model with exception "True"
    Then service metadata has a model id and operation "train"
    When i fetch the model by the name "test-model"
    Then "model" has app scope
    And I clean the project