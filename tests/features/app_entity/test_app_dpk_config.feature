Feature: Testing App custom_installation attribute

  Background:
    Given Platform Interface is initialized as dlp and Environment is set according to git branch
    And I create a project by the name of "app-custom_installation"

  @DAT-63173
  Scenario: Install app - custom_installation should be equal to published dpk.components
    Given I fetch the dpk from 'apps/app_compare_models.json' file
    When I publish a dpk to the platform
    And I install the app
    And I wait "4"
    Then I validate app.custom_installation is equal to published.dpk components
    And I uninstall the app

  @DAT-64292
  Scenario: Install app with partial custom_installation - Should install only expected services
    Given I fetch the dpk from 'apps/app_three_services.json' file
    When I publish a dpk to the platform
    And I create a context.custom_installation var
    And I remove the last service from context.custom_installation
    And I install the app with custom_installation "True"
    And I wait "4"
    Then I validate app.custom_installation is equal to composition
    And I uninstall the app

  @DAT-64293
  Scenario: Add service to custom_installation - Should extend the dpk and install the expected services
    Given I fetch the dpk from 'apps/app_three_services.json' file
    When I publish a dpk to the platform
    And I create a context.custom_installation var
    And I add service to context.custom_installation
    And I install the app with custom_installation "True"
    And I wait "4"
    And I list services in project
    Then I receive a Service list of "4" objects
    Then I validate app.custom_installation is equal to composition
    And I uninstall the app

  @DAT-64311
  @DAT-62824
  Scenario: Update installed app.custom_installation with new service - Should update composition with new service
    Given I fetch the dpk from 'apps/app_three_services.json' file
    When I publish a dpk to the platform
    And I install the app
    And I wait "4"
    And I create a context.custom_installation var
    And I add service to context.custom_installation
    And I update an app
    And I wait "4"
    Then I validate app.custom_installation is equal to composition
    And services should be updated
    And I uninstall the app

  @DAT-64312
  Scenario: Update dpk and published new version and update app - Should update get new att from dpk to composition
    Given I fetch the dpk from 'apps/app_three_services.json' file
    When I publish a dpk to the platform
    And I create a context.custom_installation var
    And I remove the last service from context.custom_installation
    And I install the app with custom_installation "True"
    And I wait "4"
    And I add att 'cooldownPeriod=500' to dpk 'service' in index '0'
    And I increment dpk version
    And I publish a dpk
    And I increment app dpk_version
    And I update an app
    Then I validate dpk autoscaler in composition for service in index '0'