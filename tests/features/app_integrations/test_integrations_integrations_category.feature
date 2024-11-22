Feature: publish a dpk with service Integration

  Background:
    Given Platform Interface is initialized as dlp and Environment is set according to git branch
    And I create a project by the name of "dpk-intg"
    And I create a dataset by the name of "integ" in the project
    And I upload item in "0000000162.jpg" to dataset


  @DAT-74185
  Scenario: publishing a dpk with integrations - integrations in module use integration category
    Given I create key value integration with key "nvidiaUser" value "category"
    Given I fetch the dpk from 'app_with_integrations/module_service_integration_category.json' file
    When I set code path "base_service_integration" to context
    And I pack directory by name "init_integrations"
    And I add codebase to dpk
    And I add integration to dpk
    And I publish a dpk to the platform
    And I install the app
    When I get service by name "run"
    Then I execute the service
    And Execution was executed and finished with status "success"
    And Execution output is "category"
    When I delete integration in context

  @DAT-81128
  Scenario: publishing a dpk with integrations in scope node - integrations in module use integration category
    Given I publish a pipeline node dpk from file "apps/app_scope_node_with_init.json" and with code path "move_item"
    When I install the app
    Then i got the dpk required integration