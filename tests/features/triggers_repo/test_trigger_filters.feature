@bot.create
Feature: Triggers repository create service testing

  Background: Initiate Platform Interface and create a project
    Given Platform Interface is initialized as dlp and Environment is set according to git branch
    And I create a project by the name of "triggers_filters"
    And I create a dataset with a random name
    And I add folder ".hidden-folder" to context.dataset

  @services.delete
  @packages.delete
  @testrail-C4523177
  @DAT-49912
  Scenario: Service - create Item Trigger with filter hidden true - Should execute on hidden items
    Given There is a package (pushed from "triggers/item") by the name of "triggers-create"
    And There is a service by the name of "triggers-create" with module name "default_module" saved to context "service"
    When I create filters
    And I add field "hidden" with values "True" and operator "None"
    And I create a trigger
      | name=triggers-create | filters=context | resource=Item | action=Created | active=True | executionMode=Once |
    Then I receive a Trigger entity
    When I upload file in path "0000000162.jpg" to remote path "/.hidden-folder"
    Then Service was triggered on "hidden-item"
    When I list service executions
    Then I receive a list of "1" executions


  @services.delete
  @packages.delete
  @testrail-C4523177
  @DAT-49912
  Scenario: Pipeline - create Item Trigger with filter hidden true - Should execute on hidden items
    Given I create pipeline with the name "pipeline"
    And I create "code" node with params
      | key      | value |
      | position | (1,1) |
    When I add and connect all nodes in list to pipeline entity
    And I add trigger to first node with params
      | key    | value |
      | hidden | True  |
    And I install pipeline in context
    And I get service in index "0"
    When I upload file in path "0000000162.png" to remote path "/.hidden-folder"
    Then Service was triggered on "hidden-item"
    When I list service executions
    Then I receive a list of "1" executions
