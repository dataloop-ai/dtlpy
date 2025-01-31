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
  @DAT-52909
  Scenario: Check Execution status finish - with sync true
    Given There is a package (pushed from "executions/status") by the name of "execution-create"
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

  @DAT-85237
  Scenario: Create Execution from app model
    Given I create a dataset with a random name
    When I upload labels to dataset
    Given I upload an item by the name of "test_item.jpg"
    Given I fetch the dpk from 'model_dpk/modelsDpks.json' file
    When I create a dummy model package by the name of "dummymodel" with entry point "main.py"
    When I create a model from package by the name of "test-model" with status "trained" in index "0"
    When I add a service to the DPK
    When I publish a dpk to the platform
    When I install the app
    And i fetch the model by the name "test-model"
    When i "deploy" the model
    When I run predict on the item with the model from the app
    When I execute the app service
    Then Both executions should have app and driverId