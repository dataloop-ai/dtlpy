@bot.create
Feature: Executions repository execution creator testing

  Background: Initiate Platform Interface and create a project
    Given Platform Interface is initialized as dlp and Environment is set according to git branch
    And I create a project by the name of "execution_creator"
    And I create a dataset with a random name

  @services.delete
  @packages.delete
  @testrail-C4533878
  Scenario: Created Item Execution - Execution creator should be the current user
    Given There is a package (pushed from "executions/item") by the name of "execution-create"
    And There is a service by the name of "executions-creator" with module name "default_module" saved to context "service"
    And I upload item in "0000000162.jpg" to dataset
    When I create an execution with "inputs"
      | sync=False | inputs=Item |
    Then I receive an Execution entity
    And I validate execution params
      | key     | value        |
      | creator | current_user |

  @services.delete
  @packages.delete
  @testrail-C4533878
  Scenario: Created Item Execution by trigger event - Execution creator should be piper user
    Given There is a package (pushed from "executions/item") by the name of "execution-create"
    And There is a service by the name of "executions-creator" with module name "default_module" saved to context "service"
    When I create a trigger
      | name=triggers-create | filters=None | resource=Item | action=Created | active=True | executionMode=Once |
    Then I receive a Trigger entity
    When I upload item in "0000000162.jpg"
    And I get service execution by "item.id"
    Then I validate execution params
      | key     | value             |
      | creator | piper@dataloop.ai |

  @pipelines.delete
  @testrail-C4533878
  Scenario: Pipeline - Created Item Execution - Execution creator should be current user
    Given I create pipeline with the name "pipeline"
    And I create "dataset" node with params
      | key      | value |
      | position | (1,1) |
    And I create "dataset" node with params
      | key      | value |
      | position | (2,2) |
    When I add and connect all nodes in list to pipeline entity
    And I install pipeline in context
    And I upload item in "0000000162.jpg"
    And I execute pipeline with input type "Item"
    Then I validate pipeline execution params include node executions "True"
      | key     | value        |
      | creator | current_user |

  @pipelines.delete
  @testrail-C4533878
  Scenario: Pipeline - Created Item Execution trigger event - Execution creator should be current user
    Given I create pipeline with the name "pipeline"
    And I create "dataset" node with params
      | key      | value |
      | position | (1,1) |
    And I create "dataset" node with params
      | key      | value |
      | position | (2,2) |
    When I add and connect all nodes in list to pipeline entity
    And I add trigger to first node with params
      | key | value |
    And I install pipeline in context
    And I upload item in "0000000162.jpg"
    Then I wait "5"
    When I get pipeline cycle execution in index "0"
    Then I validate pipeline execution params include node executions "True"
      | key     | value             |
      | creator | piper@dataloop.ai |
