@bot.create
Feature: Executions repository create service testing

  Background: Initiate Platform Interface and create a project
    Given Platform Interface is initialized as dlp and Environment is set according to git branch
    And I create a project by the name of "execution_create"
    And I create a dataset with a random name

  @services.delete
  @packages.delete
  @testrail-C4523101
  @DAT-46518
  Scenario: Created Item Execution - Execution input object - sync
    Given There is a package (pushed from "executions/item") by the name of "execution-create"
    And There is a service by the name of "executions-create" with module name "default_module" saved to context "service"
    And I upload item in "0000000162.jpg" to dataset
    When I create an execution with "inputs"
      | sync=False | inputs=Item |
    Then I receive an Execution entity
    Then Execution was executed on "item"

  @services.delete
  @packages.delete
  @testrail-C4523101
  @DAT-46518
  Scenario: Created Item Execution - Execution input params - sync
    Given There is a package (pushed from "executions/item") by the name of "execution-create"
    And There is a service by the name of "executions-create" with module name "default_module" saved to context "service"
    And I upload item in "0000000162.jpg" to dataset
    When I create an execution with "inputs"
      | sync=False | inputs=Item |
    Then I receive an Execution entity
    Then Execution was executed on "item"

  @services.delete
  @packages.delete
  @testrail-C4523101
  @DAT-46518
  Scenario: Created Item Execution - Execution input params - async
    Given There is a package (pushed from "executions/item") by the name of "execution-create"
    And There is a service by the name of "executions-create" with module name "default_module" saved to context "service"
    And I upload item in "0000000162.jpg" to dataset
    When I create an execution with "params"
      | sync=False | inputs=Item |
    Then I receive an Execution entity
    Then Execution was executed on "item"

  @services.delete
  @packages.delete
  @testrail-C4523101
  @DAT-46518
  Scenario: Created Item Execution for multiple modules and functions - sync
    Given There is a package (pushed from "executions/multiple_modules_functions") by the name of "execution-create"
    And There is a service by the name of "executions-create-first" with module name "first" saved to context "first_service"
    And There is a service by the name of "executions-create-second" with module name "second" saved to context "second_service"
    And I upload item in "0000000162.jpg" to dataset
    When I create an execution for all functions
    Then Execution was executed on item for all functions

  @services.delete
  @packages.delete
  @testrail-C4523101
  @DAT-46518
  Scenario: Created Item Execution - with sync true
    Given There is a package (pushed from "executions/item") by the name of "execution-create"
    And There is a service by the name of "executions-create" with module name "default_module" saved to context "service"
    And I upload item in "0000000162.jpg" to dataset
    When I create an execution with "inputs"
      | sync=True | inputs=Item |
    Then I receive an Execution entity
    Then Execution was executed and finished with status "success"

  @services.delete
  @packages.delete
  @DAT-53072
  Scenario: Created Item Execution - with id that ends with e28
    Given A service that receives items input
    When I create an execution with "inputs"
      | sync=True | inputs=e28 |
    Then I receive an Execution entity
    Then Execution input is a valid itemId
