@bot.create
Feature: Triggers repository create service testing

  Background: Initiate Platform Interface and create a project
    Given Platform Interface is initialized as dlp and Environment is set according to git branch
    And I create a project by the name of "triggers_create"
    And I create a dataset with a random name

  @services.delete
  @packages.delete
  @testrail-C4523177
  @DAT-46640
  Scenario: Created Item Trigger
    Given There is a package (pushed from "triggers/item") by the name of "triggers-create"
    And There is a service by the name of "triggers-create" with module name "default_module" saved to context "service"
    When I create a trigger
      | name=triggers-create | filters=None | resource=Item | action=Created | active=True | executionMode=Once |
    Then I receive a Trigger entity
    When I upload item in "0000000162.jpg" to dataset
    Then Service was triggered on "item"
    When I list service executions
    Then I receive a list of "1" executions

  @services.delete
  @packages.delete
  @testrail-C4523177
  @DAT-46640
  Scenario: Created Item Trigger - specified function name
    Given There is a package (pushed from "triggers/function_name") with function "train"
    And There is a service by the name of "triggers-create" with module name "default_module" saved to context "service"
    When I create a trigger
      | name=triggers-create | filters=None | resource=Item | action=Created | active=True | executionMode=Once | function_name=train |
    Then I receive a Trigger entity
    When I upload item in "0000000162.jpg" to dataset
    Then Service was triggered on "item"

  @services.delete
  @packages.delete
  @testrail-C4523177
  @DAT-46640
  Scenario: Updated Item Trigger
    Given There is a package (pushed from "triggers/item") by the name of "triggers-create"
    And There is a service by the name of "triggers-create" with module name "default_module" saved to context "service"
    When I upload item in "0000000162.jpg" to dataset
    Then I wait "7"
    When I create a trigger
      | name=triggers-create | filters=None | resource=Item | action=Updated | active=True | executionMode=Once |
    Then I receive a Trigger entity
    When I edit item user metadata
    Then Service was triggered on "item"
