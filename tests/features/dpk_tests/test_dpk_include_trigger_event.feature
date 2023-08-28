Feature: publish a dpk with trigger

  Background:
    Given Platform Interface is initialized as dlp and Environment is set according to git branch
    And I create a project by the name of "dpk-triggers"
    And I create a dataset by the name of "model" in the project


  @DAT-49643
  Scenario: publishing a dpk with item event trigger
    Given I fetch the dpk from 'apps/app_include_trigger.json' file
    When I set code path "packages_get" to context
    And I pack directory by name "packages_get"
    And I add codebase to dpk
    And I publish a dpk to the platform
    And I install the app
    And I set the trigger in the context
    And I upload item in "0000000162.jpg" to dataset
    And I set the execution in the context
    Then I receive a Trigger entity
    And Service was triggered on "item"
    And Execution was executed and finished with status "success"
    When I try to update trigger
      | active=False |
    Then Trigger attributes are modified
      | active=False |
    When I pause service in context
    Then I uninstall the app


  @DAT-49643
  Scenario: publishing a dpk with item event trigger and filter
    Given I fetch the dpk from 'apps/app_include_filters_trigger.json' file
    When I set code path "packages_get" to context
    And I pack directory by name "packages_get"
    And I add codebase to dpk
    And I publish a dpk to the platform
    And I install the app
    And I set the trigger in the context
    And I upload item in "0000000162.png" to dataset
    And I set the execution in the context
    Then I receive a Trigger entity
    And Service was triggered on "item"
    And Execution was executed and finished with status "success"
    And I uninstall the app
