Feature: publish a dpk with service Integration

  Background:
    Given Platform Interface is initialized as dlp and Environment is set according to git branch
    And I create a project by the name of "dpk-intg"
    And I create a dataset by the name of "integ" in the project
    And I upload item in "0000000162.jpg" to dataset


  @DAT-74467
  Scenario: publishing a dpk with integrations - integrations in service
    Given I create key value integration with key "nvidiaUser" value "inservice"
    Given I fetch the dpk from 'app_with_integrations/service_integration.json' file
    When I set code path "base_service_integration" to context
    And I pack directory by name "init_integrations"
    And I add codebase to dpk
    And I add integration to dpk
    And I publish a dpk to the platform
    And I install the app
    When I get service by name "run"
    Then I execute the service
    And Execution was executed and finished with status "success"
    And Execution output is "inservice"
    When I delete integration in context
    And I uninstall the app

  @DAT-75930
  Scenario: publishing a dpk with integrations optional - integrations in service should able to install
    Given I fetch the dpk from 'app_with_integrations/service_integration.json' file
    And I remove the "value" from integration from the dpk in "services" component in index 0
    And I add "optional=True" to integration from the dpk in "services" component in index 0
    When I set code path "base_service_integration" to context
    And I pack directory by name "init_integrations"
    And I add codebase to dpk
    And I publish a dpk to the platform
    And I install the app
