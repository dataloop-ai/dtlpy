@bot.create
Feature: Services repository update with force=True service testing

  Background: Initiate Platform Interface and create a project
    Given Platform Interface is initialized as dlp and Environment is set according to git branch
    And I create a project by the name of "services_update"
    And I create a dataset with a random name

  @services.delete
  @packages.delete
  @testrail-C4532327
  @DAT-46618
  Scenario: Update service with force - Execution should stop immediately
    Given There is a package (pushed from "services/long_term") by the name of "services-update"
    And There is a service with max_attempts of "1" by the name of "services-update-force" with module name "default_module" saved to context "service"
    And I execute service
    And Execution is running
    When I update service with force="True"
    Then Execution stopped immediately


  @services.delete
  @packages.delete
  @DAT-70898
  Scenario: Update service with force - Execution logs should restart
    Given There is a package (pushed from "services/execution_progress") by the name of "execution-progress"
    And There is a service by the name of "executions-create" with module name "default_module" saved to context "service"
    And I execute service
    And Execution is running
    When I update service with force="True"
    Then I expect execution status progress include "10" in "percentComplete" with a frequency of "2"
