@bot.create
Feature: Executions repository rerun execution

  Background: Initiate Platform Interface and create a project
    Given Platform Interface is initialized as dlp and Environment is set according to git branch
    And I create a project by the name of "execution_rerun"
    And I create a dataset with a random name

  @services.delete
  @packages.delete
  @DAT-52700
  Scenario: Rerun execution should take te latest package revision
    Given There is a package (pushed from "executions/item") by the name of "execution-rerun"
    And There is a service by the name of "executions-rerun" with module name "default_module" saved to context "service"
    And I upload item in "0000000162.jpg" to dataset
    When I create an execution with "inputs"
      | sync=False | inputs=Item |
    Then I receive an Execution entity
    Then Execution was executed on "item"
    And I validate execution response params
      | key             | value |
      | packageRevision | 1.0.0 |
    When I update package
    And I update service to latest package revision
    And I rerun the execution
    Then I validate execution response params
      | key             | value |
      | packageRevision | 1.0.1 |
    Then Execution was executed on "item"




