@qa-nightly
@bot.create
@rc_only
Feature: Executions repository create service testing

  Background: Initiate Platform Interface and create a project
    Given Platform Interface is initialized as dlp and Environment is set according to git branch
    And I create a project by the name of "requirements_error"
    And I create a dataset with a random name

  @services.delete
  @packages.delete
  @DAT-46788
  Scenario: Requirements error should raise notification
    Given There is a package (pushed from "faas/initError") by the name of "requirements-error"
    And There is a service by the name of "requirements-error" with module name "default_module" saved to context "service"
    And I add bad requirements to service
    When Service minimum scale is "1"
    Then I receive "RequirementsError" notification with resource "service.id"
    And Service is deactivated by system