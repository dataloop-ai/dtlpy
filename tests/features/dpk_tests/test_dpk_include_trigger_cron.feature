Feature: publish a dpk with trigger

  Background:
    Given Platform Interface is initialized as dlp and Environment is set according to git branch
    And I create a project by the name of "dpk-triggers"
    And I create a dataset by the name of "model" in the project


  @DAT-50148
  Scenario: publishing a dpk with cron trigger
    Given I fetch the dpk from 'apps/app_include_cron_trigger.json' file
    When I set code path "packages_get" to context
    And I pack directory by name "packages_get"
    And I add codebase to dpk
    And I publish a dpk to the platform
    And I install the app
    And I set the trigger in the context
    Then I receive a CronTrigger entity
    When I list service executions
    Then I wait until I receive a list of "1" executions
    And I uninstall the app


  @DAT-52535
  Scenario: publishing a dpk with cron trigger and input
    Given I fetch the dpk from 'apps/app_include_cron_trigger_with_input.json' file
    When I update dpk dtlpy to current version for service in index 0
    When I set code path "triggers/cron_string" to context
    And I pack directory by name "cron_string"
    And I add codebase to dpk
    And I publish a dpk to the platform
    And I install the app
    And I set the trigger in the context
    Then I receive a CronTrigger entity
    And Service was triggered on "string"
    And Execution was executed and finished with status "success"
    And I uninstall the app