@qa-nightly
@bot.create
Feature: Executions repository create service testing

  Background: Initiate Platform Interface and create a project
    Given Platform Interface is initialized as dlp and Environment is set according to git branch
    And I create a project by the name of "import_error"
    And I create a dataset with a random name

  @services.delete
  @packages.delete
  @DAT-46784
  Scenario: Init error should raise notification
    Given There is a package (pushed from "faas/importError") by the name of "import-error"
    And There is a service by the name of "import-error" with module name "default_module" saved to context "service"
    When Service minimum scale is "1"
    Then I receive "RequirementsError" notification
    And Service is deactivated by system
