@bot.create
Feature: Cron Triggers repository create service testing

  Background: Initiate Platform Interface and create a project
    Given Platform Interface is initialized as dlp and Environment is set according to git branch
    And I create a project by the name of "triggers_cron_create"
    And I create a dataset with a random name


  @services.delete
  @packages.delete
  @testrail-C4530457
  Scenario: Get cron execution
    Given There is a package (pushed from "triggers/item") by the name of "triggers-cron"
    And There is a service by the name of "triggers-cron" with module name "default_module" saved to context "service"
    And I create a cron trigger
      | name=triggers-create | function_name=run | cron=* * * * * |
    When I list service executions
    Then I receive a list of "0" executions
    And I wait "60"
    When I list service executions
    Then I receive a list of "1" executions
    And I wait "60"
    When I list service executions
    Then I receive a list of "2" executions
    When I delete trigger by "id"

