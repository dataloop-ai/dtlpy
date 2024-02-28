Feature: Models repository flow testing

  Background: Initiate Platform Interface and create a project
    Given Platform Interface is initialized as dlp and Environment is set according to git branch
    And I create a project by the name of "model_mgmt"
    And I create a dataset with a random name
    And I upload an item by the name of "test_item.jpg"
    When I upload labels to dataset
    And I upload "5" box annotation to item


  @DAT-53071
  Scenario: test evaluate service updated
    Given I fetch the dpk from 'model_dpk/modelsDpks.json' file
    When I create a dummy model package by the name of "dummymodel" with entry point "main.py"
    And I create a model from package by the name of "test-model-eve" with status "trained" in index "0"
    And I publish a dpk to the platform
    And I install the app
    And i fetch the model by the name "test-model-eve"
    And i add a Service config runtime
      | runnerImage=ImageA | podType=regular-xs |
    When i "evaluate" the model
    Then check service runtime
      | runnerImage=ImageA | podType=regular-xs |
    When i add a Service config runtime
      | runnerImage=ImageB | podType=regular-s |
    When i "evaluate" the model
    Then check service runtime
      | runnerImage=ImageB | podType=regular-s |
