Feature: Pipeline resource multiples inputs testing

  Background: Initiate Platform Interface and create a pipeline
    Given Platform Interface is initialized as dlp and Environment is set according to git branch
    And I create a project by the name of "pipeline_multiple_inputs"
    And I create a dataset with a random name
    When I create a new plain recipe
    And I update dataset recipe to the new recipe


  @pipelines.delete
  @testrail-C4536827
  @DAT-46588
  Scenario: Multiple inputs - Input with connector and input with default param - Should use the default param
    Given I create pipeline from json in path "pipelines_json/inputs_default_and_connector.json"
    And I install pipeline in context
    When I upload item in "0000000162.jpg" to pipe dataset
    And I execute pipeline with input type "Item"
    Then Pipeline has "1" cycle executions
    And I expect that pipeline execution has "2" success executions
    And I validate pipeline executions params
      | key   | value                                                    |
      | input | {"item": {"item_id": "item.id"}}                         |
      | input | {"item": {"item_id": "item.id"}, "text" : "Hello World"} |

  @pipelines.delete
  @testrail-C4536827
  @DAT-46588
  Scenario: Multiple inputs - Input with connector and input with connector - Should wait for two inputs
    Given I create pipeline from json in path "pipelines_json/inputs_wait_for_two.json"
    And I install pipeline in context
    When I upload item in "0000000162.jpg" to pipe dataset
    And I execute pipeline with input type "Item"
    Then Pipeline has "1" cycle executions
    And I expect that pipeline execution has "4" success executions
    And I validate pipeline executions params
      | key   | value                                                                        |
      | input | {"item": {"item_id": "item.id"}, "dataset_id": "dataset.id", "folder": None} |
      | input | {"item": {"item_id": "item.id"}, "dataset_id": "dataset.id", "folder": None} |
      | input | {"item": {"item_id": "item.id"}, "dataset_id": "dataset.id", "folder": None} |
      | input | {"item": {"item_id": "item.id"}, "item_1": {"item_id": "item.id"}}           |

  @pipelines.delete
  @testrail-C4536827
  @DAT-46588
  Scenario: Multiple inputs - Input with connector and input-list with connector - Should duplicate executions according to list
    Given I create pipeline from json in path "pipelines_json/inputs_item_and_annotations.json"
    And I install pipeline in context
    And Item in path "assets_split/annotations_upload/0000000162.jpg" is uploaded to "Dataset"
    When Item is annotated with annotations in file: "assets_split/annotations_upload/annotations_new.json"
    And I execute pipeline with input type "Item"
    Then Pipeline has "1" cycle executions
    And I expect that pipeline execution has "9" success executions


  @pipelines.delete
  @testrail-C4536827
  @DAT-46588
  Scenario: Multiple inputs - Input-list with connector and input-list with connector - with same length - Should create one execution
    Given There are "4" items
    And I create pipeline from json in path "pipelines_json/inputs_items_list_same_size.json"
    And I install pipeline in context
    When I upload item in "0000000162.jpg" to pipe dataset
    And I execute pipeline with input type "Item"
    Then Pipeline has "1" cycle executions
    And I expect that pipeline execution has "6" success executions


  @pipelines.delete
  @testrail-C4536827
  @DAT-46588
  Scenario: Multiple inputs - Input-list with connector and input-list with connector - with different length - Should failed
    Given There are "4" items
    And I create pipeline from json in path "pipelines_json/inputs_items_list_different_size.json"
    And I install pipeline in context
    When I upload item in "0000000162.jpg" to pipe dataset
    And I execute pipeline with input type "Item"
    And I get pipeline execution in index "0"
    Then I validate Cycle execution status is "failed"

