Feature: Pipeline entity method testing

  Background: Initiate Platform Interface and create a pipeline
    Given Platform Interface is initialized as dlp and Environment is set according to git branch
    And I create a project by the name of "test_pipeline_flow"
    And I create a dataset with a random name
    And I upload item in "0000000162.jpg" to dataset


  @pipelines.delete
  @testrail-C4533385
  @DAT-46573
  Scenario: pipeline execute batch
    Given I upload item by the name of "test_item.jpg" to a remote path "test"
    And I upload item by the name of "test_item2.jpg" to a remote path "test"
    When I create a new plain recipe
    And I update dataset recipe to the new recipe
    When I create a pipeline with name "test_pipeline_execute"
    And I add a code node to the pipeline
    When I execute the pipeline batch items
    Then pipeline execution are success in "2" items

  @services.delete
  @packages.delete
  @testrail-C4533386
  @DAT-46573
  Scenario: service execute batch
    Given I upload item by the name of "test_item.jpg" to a remote path "test"
    And I upload item by the name of "test_item2.jpg" to a remote path "test"
    When I create a new plain recipe
    And I update dataset recipe to the new recipe
    Given There is a package (pushed from "services/item_with_init") by the name of "services-flow"
    When I deploy a service with init prams
    And I execute the service batch items
    Then service execution are success in "2" items

  @pipelines.delete
  @DAT-80459
  Scenario: Execute pipeline from a specific node
    Given I install a pipeline with 2 dataset nodes
    When I execute the second node which is not the root node
    Then Then pipeline should start from the requested node


  @DAT-87313
  Scenario: app service execute batch
    Given I upload item by the name of "test_item.jpg" to a remote path "test"
    And I upload item by the name of "test_item2.jpg" to a remote path "test"
    When I create a new plain recipe
    And I update dataset recipe to the new recipe
    Given I fetch the dpk from 'apps/app_move_item_service.json' file
    When I set code path "move_item" to context
    And I pack directory by name "move_item"
    And I add codebase to dpk
    And I publish a dpk
    And I install the app
    When I get service in index "0"
    And I execute the full dataset items on function "move_item"
    Then service execution are success in "3" items


  @pipelines.delete
  @DAT-91921
  Scenario: pipeline execute batch
    Given There are items, path = "filters/image.jpg"
      | directory={"/": 3, "/dir1/": 3, "/dir1/dir2/": 3} | annotated_label={"dog": 3, "cat": 3} | annotated_type={"box": 3, "polygon": 3} |
    When I create filters
    And I join field "label" with values "dog" and operator "None"
    When I create a pipeline with name "test_pipeline_execute"
    And I add a code node to the pipeline
    When I execute the pipeline batch items with "context.filters"
    Then pipeline execution are success in "3" items