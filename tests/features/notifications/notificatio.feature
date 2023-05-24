@qa-nightly
@bot.create
Feature: Executions repository create service testing

  Background: Initiate Platform Interface and create a project
    Given Platform Interface is initialized as dlp and Environment is set according to git branch
    And I create a project by the name of "execution_create"
    And I create a dataset with a random name

  @services.delete
  @packages.delete
  @DAT-46784
  Scenario: Init error should raise notification
    Given There is a package (pushed from "faas/importError") by the name of "import-error"
    And There is a service by the name of "import-error" with module name "default_module" saved to context "service"
    And I upload item in "0000000162.jpg" to dataset
    When I create an execution with "inputs"
      | sync=False | inputs=Item |
    Then I receive "RequirementsError" notification
    And Service is deactivated by system

  @services.delete
  @packages.delete
  @DAT-46785
  Scenario: Import error should raise notification
    Given There is a package (pushed from "faas/initError") by the name of "init-error"
    And There is a service by the name of "init-error" with module name "default_module" saved to context "service"
    And I upload item in "0000000162.jpg" to dataset
    When I create an execution with "inputs"
      | sync=False | inputs=Item |
    Then I receive "InitError" notification
    And Service is deactivated by system

  @services.delete
  @packages.delete
  @DAT-46786
  Scenario: Docker Image error should raise notification
    Given There is a package (pushed from "faas/initError") by the name of "imagepullback-error"
    And There is a service by the name of "imagepullback-error" with module name "default_module" saved to context "service"
    And Service has wrong docker image
    And I upload item in "0000000162.jpg" to dataset
    When I create an execution with "inputs"
      | sync=False | inputs=Item |
    Then I receive "ImagePullBackOff" notification
    And Service is deactivated by system

  @services.delete
  @packages.delete
  @DAT-46787
  Scenario: Code base error should raise notification
    Given There is a package (pushed from "faas/initError") by the name of "codebase-error"
    And There is a service by the name of "codebase-error" with module name "default_module" saved to context "service"
    And I delete service code base
    And I upload item in "0000000162.jpg" to dataset
    When I create an execution with "inputs"
      | sync=False | inputs=Item |
    Then I receive "CodebaseError" notification
    And Service is deactivated by system

  @services.delete
  @packages.delete
  @DAT-46788
  Scenario: Requirements error should raise notification
    Given There is a package (pushed from "faas/initError") by the name of "requirements-error"
    And There is a service by the name of "requirements-error" with module name "default_module" saved to context "service"
    And I add bad requirements to service
    And I upload item in "0000000162.jpg" to dataset
    When I create an execution with "inputs"
      | sync=False | inputs=Item |
    Then I receive "RequirementsError" notification
    And Service is deactivated by system