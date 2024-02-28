@qa-nightly
@bot.create
@rc_only
Feature: Executions repository create service testing

  Background: Initiate Platform Interface and create a project
    Given Platform Interface is initialized as dlp and Environment is set according to git branch
    And I create a project by the name of "oom_error"
    And I create a dataset with a random name

  @services.delete
  @packages.delete
  @DAT-25330
  Scenario: Init error should raise notification
    Given There is a package (pushed from "faas/oomError") by the name of "oom-error"
    And There is a service by the name of "oom-error" with module name "default_module" saved to context "service"
    And I upload item in "0000000162.jpg" to dataset
    When I create an execution with "inputs"
      | sync=False | inputs=Item |
    Then I receive an Execution entity
    Then I receive "ExecutionFailed" notification with resource "execution.id"
    And Execution was executed and finished with status "failed" and message "Execution has reached max attempts"


