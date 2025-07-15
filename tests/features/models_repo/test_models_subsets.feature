Feature: Models repository subset testing

  Background: Initiate Platform Interface and create a project
    Given Platform Interface is initialized as dlp and Environment is set according to git branch
    And I create a project by the name of "model_mgmt"
    And I create a dataset with a random name

 @DAT-97046
 Scenario: test model annotations subset
   Given I fetch the dpk from 'apps/app_models_subsets.json' file
   And I publish a dpk to the platform
   When I install the app with custom_installation "False"
   And i fetch the model by the name "withAnnotations"
   Then Model "train" filter should not be empty
   Then Model "validation" filter should not be empty
   Then Model "annotations" filter should not be empty
   When i fetch the model by the name "withOutAnnotations"
   Then Model "train" filter should not be empty
   Then Model "validation" filter should not be empty
   Then Model "annotations" filter should be empty
   And I clean the project

 @DAT-97832
 Scenario: test model annotations subset from update dpk
   Given I fetch the dpk from 'apps/app_models_subsets.json' file
   And I publish a dpk to the platform
   Given I fetch the dpk from 'apps/app_models_subsets.json' file and update dpk with params 'True' convert to dict 'True'
     | key                                         | value                                                                                                                                                                                                                                                                                                                                                                 |
     | components.models.0.metadata.system.annotationsSubsets | {"all": {"filter": {"$and": [{"type": "box"}]}, "page": 0, "pageSize": 1000, "resource": "annotations"}} |
   And I publish a dpk to the platform
   When I install the app with custom_installation "False"
   And i fetch the model by the name "withAnnotations"
   Then Model "train" filter should not be empty
   Then Model "validation" filter should not be empty
   Then Model "annotations" filter should not be empty
   When i fetch the model by the name "withOutAnnotations"
   Then Model "train" filter should not be empty
   Then Model "validation" filter should not be empty
   Then Model "annotations" filter should not be empty
   And I clean the project

 @DAT-97833
 Scenario: Auto update - update the app with model subset - Should update the already models subsets
   Given I fetch the dpk from 'apps/app_models_subsets.json' file
   And I publish a dpk to the platform
   When I install the app with custom_installation "False"
   And I update app auto update to "True"
   Given I fetch the dpk from 'apps/app_models_subsets.json' file and update dpk with params 'True' convert to dict 'True'
     | key                                         | value                                                                                                                                                                                                                                                                                                                                                                 |
     | components.models.0.metadata.system.annotationsSubsets | {"all": {"filter": {"$and": [{"type": "box"}]}, "page": 0, "pageSize": 1000, "resource": "annotations"}} |
   And I publish a dpk to the platform
   When i fetch the model by the name "withAnnotations"
   Then Model "train" filter should not be empty
   Then Model "validation" filter should not be empty
   Then Model "annotations" filter should not be empty
   When i fetch the model by the name "withOutAnnotations"
   Then Model "train" filter should not be empty
   Then Model "validation" filter should not be empty
   Then Model "annotations" filter should be empty
   And I clean the project


  @DAT-97834
  Scenario: test model add annotations to model subset - Should add annotation subsets
    Given I upload an item by the name of "test_item.jpg"
    When I upload labels to dataset
    And I upload "5" box annotation to item
    Given I fetch the dpk from 'apps/app_models_subsets.json' file
    When I set code path "models_flow" to context
    And I pack directory by name "models_flow"
    And I add codebase to dpk
    And I publish a dpk to the platform
    When I install the app with custom_installation "False"
    And i fetch the model by the name "withAnnotations"
    Then Model "train" filter should not be empty
    Then Model "validation" filter should not be empty
    Then Model "annotations" filter should not be empty
    When i fetch the model by the name "withOutAnnotations"
    And I add "annotations" filter with resource "annotations" to the model
    Then Model "train" filter should not be empty
    Then Model "validation" filter should not be empty
    Then Model "annotations" filter should not be empty
    When i fetch the model by the name "withAnnotations"
    When I add dataset to model
    When i "train" the model
    Then model status should be "trained" with execution "True" that has function "train_model"
    And I clean the project


 @skip_test 
 @DAT-97735
  Scenario: Model with annotations subset created from pipeline - Execution should be successful
    Then Add Multiple Labels "Number", "Letters", "Unknown"
    When I upload all items and annotations from directory "10_items_annotations"
    Given I fetch the dpk from 'model_dpk/modelsDpks.json' file
    When I create a dummy model package by the name of "dummymodel" with entry point "main.py"
    And I create a model from package by the name of "test-model" with status "created" in index "0"
    And I publish a dpk to the platform
    And I install the app
    And i fetch the model by the name "test-model"
    When I add annotation subset to model with filter '{"type": "box"}'
    Given I create pipeline from json in path "pipelines_json/pipeline_train_node.json"
    And I install pipeline in context
    When I execute pipeline with input type "None"
    Then I expect that pipeline execution has "1" success executions
    And I create filters
    And I join field "type" with values "box" and operator "None"
    And I list items with filters
    And I save the list of items as "box_items"

    # List items with qa_train metadata
    When I create filters
    And I add field "metadata.user.qa_train" with values "True" and operator "None"
    And I list items with filters
    And I save the list of items as "qa_train_items"

    # Compare the two lists
    Then The list "box_items" should match the list "qa_train_items"
