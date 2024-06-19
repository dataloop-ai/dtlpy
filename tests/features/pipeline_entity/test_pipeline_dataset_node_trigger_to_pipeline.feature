Feature: Pipeline entity method testing - Dataset node data execution

  Background: Initiate Platform Interface and create a pipeline
    Given Platform Interface is initialized as dlp and Environment is set according to git branch
    And I create a project by the name of "pipeline_dataset_node_data_execution"
    And I create a dataset with a random name
    When I create a new plain recipe
    And I update dataset recipe to the new recipe
    When I upload the file in path "assets_split/items_upload/0000000162.jpg" with remote name "1.jpg"


  @pipelines.delete
  @DAT-70527
  Scenario: Successful dataset node data execution - without filter
    Given I create pipeline with the name "pipeline"
    And I create "dataset" node with params
      | key      | value |
      | position | (1,1) |
      | load_existing_data | true |
    And I create "code" node with params
      | key      | value |
      | position | (1,1) |
    When I add and connect all nodes in list to pipeline entity
    And I install pipeline in context
    Then The dataset node is marked as triggered
    And The dataset node is assigned with a command id
    And The pipeline has been executed "1" times
    And The uploaded item has "2" executions

  @pipelines.delete
  @DAT-70527
  Scenario: Successful dataset node data execution - with filter
    Given I create pipeline with the name "pipeline"
    And I create "dataset" node with params
      | key      | value |
      | position | (1,1) |
      | load_existing_data | true |
      | data_filters       | {"$and": [{"hidden": false}, {"type": "file"}]} |
    And I create "code" node with params
      | key      | value |
      | position | (1,1) |
    When I add and connect all nodes in list to pipeline entity
    And I install pipeline in context
    Then The dataset node is marked as triggered
    And The dataset node has data_filters
    And The dataset node is assigned with a command id
    And The pipeline has been executed "1" times
    And The uploaded item has "2" executions


    @pipelines.delete
    @DAT-70527
    Scenario: Failed dataset node data execution - In-port connection error
      Given I create pipeline with the name "pipeline"
      And I create "code" node with params
        | key      | value |
        | position | (1,1) |
      And I create "dataset" node with params
        | key      | value |
        | position | (1,1) |
        | load_existing_data | true |
      And I create "code" node with params
        | key      | value |
        | position | (1,1) |
      When I add and connect all nodes in list to pipeline entity
      And I try to install pipeline in context
      Then I should get an exception error='400'
      And The pipeline has been executed "0" times
      And The uploaded item has "0" executions


  @pipelines.delete
  @DAT-70527
  Scenario: Successful dataset node data execution - Should execute only once
    Given I create pipeline with the name "pipeline"
    And I create "dataset" node with params
      | key      | value |
      | position | (1,1) |
      | load_existing_data | true |
    And I create "code" node with params
      | key      | value |
      | position | (2,2) |
    When I add and connect all nodes in list to pipeline entity
    And I install pipeline in context
    Then The dataset node is marked as triggered
    And The dataset node is assigned with a command id
    And The pipeline has been executed "1" times
    And The uploaded item has "2" executions
    When I pause pipeline in context
    And I install pipeline in context
    Then The pipeline has been executed "1" times
    And The uploaded item has "2" executions