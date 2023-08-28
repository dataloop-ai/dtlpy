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
  Scenario: Created Annotation Trigger
    Given There is a package (pushed from "triggers/annotation") by the name of "triggers-create"
    And There is a service by the name of "triggers-create" with module name "default_module" saved to context "service"
    When I upload item in "0000000162.jpg" to dataset
    And I create a trigger
      | name=triggers-create | filters=None | resource=Annotation | action=Created | active=True | executionMode=Once |
    Then I receive a Trigger entity
    When I annotate item
    Then Service was triggered on "annotation"

  @services.delete
  @packages.delete
  @testrail-C4523177
  @DAT-46640
  Scenario: Created Item clone Trigger
    Given There is a package (pushed from "triggers/item") by the name of "triggers-create"
    And There is a service by the name of "triggers-create" with module name "default_module" saved to context "service"
    When I create a trigger
      | name=triggers-clone | filters=None | resource=Item | action=Clone | active=True | executionMode=Once |
    Then I receive a Trigger entity
    When I upload item in "0000000162.jpg" to dataset
    And  I clone item to dataset
    Then Service was triggered on "itemclone"


  @services.delete
  @packages.delete
  @testrail-C4523177
  @DAT-50229
  Scenario: Created Item Trigger with wrong action - Should raise error
    Given There is a package (pushed from "triggers/item") by the name of "triggers-create"
    And There is a service by the name of "triggers-create" with module name "default_module" saved to context "service"
    When I create a trigger
      | name=triggers-clone | filters=None | resource=Item | action=statusChanged | active=True | executionMode=Always |
    Then "BadRequest" exception should be raised
    And "Received an unsupported action type as input, type: statusChanged for resource type: Item" in error message