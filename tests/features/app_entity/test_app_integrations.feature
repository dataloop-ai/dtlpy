Feature: publish a dpk with trigger

  Background:
    Given Platform Interface is initialized as dlp and Environment is set according to git branch
    And I create a project by the name of "dpk-intg"
    And I create a dataset by the name of "integ" in the project
    And I upload item in "0000000162.jpg" to dataset


  @DAT-70200
  Scenario: publishing a dpk with integrations
    Given I create "key_value" integration with name "init_integrations"
    Given I fetch the dpk from 'apps/app_service_init_intg.json' file
    When I set code path "init_integrations" to context
    And I pack directory by name "init_integrations"
    And I add codebase to dpk
    And I add integration to dpk
    And I publish a dpk to the platform
    And I install the app
    When I get service by name "run"
    Then I execute the service
    And Execution was executed and finished with status "success"
    When I delete integration in context

  @DAT-70200
  Scenario: publishing a package with secrets
    Given I create "key_value" integration with name "init_service_integrations"
    And I create a package with secrets with entry point "init_integrations"
    Then I execute the service
    And Execution was executed and finished with status "success"
    And service has integrations
    When I delete integration in context