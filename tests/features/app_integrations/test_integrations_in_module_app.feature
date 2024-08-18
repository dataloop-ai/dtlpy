Feature: publish a dpk with service Integration

  Background:
    Given Platform Interface is initialized as dlp and Environment is set according to git branch
    And I create a project by the name of "dpk-intg"
    And I create a dataset by the name of "integ" in the project
    And I upload item in "0000000162.jpg" to dataset


  @DAT-74467
  Scenario: publishing a app with integrations - integrations in app module
    Given I create key value integration with key "nvidiaUser" value "inapp"
    Given I fetch the dpk from 'app_with_integrations/module_service_integration_without_value.json' file
    When I set code path "base_service_integration" to context
    And I pack directory by name "init_integrations"
    And I add codebase to dpk
    And I publish a dpk to the platform
    And I install the app with integration
    When I get service by name "run"
    Then I execute the service
    And Execution was executed and finished with status "success"
    And Execution output is "inapp"
    When I delete integration in context