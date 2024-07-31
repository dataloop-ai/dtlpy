Feature: App entity Install App

  Background: Initialize
    Given Platform Interface is initialized as dlp and Environment is set according to git branch
    And I create a project by the name of "test_app_install"

  @testrail-C4524925
  @DAT-46453
  Scenario: Install a valid app
    Given I have an app entity from "apps/app.json"
    And publish the app
    When I install the app
    Then I should get the app with the same id
    When I install the app with exception
    Then I should get an exception error='400'
    And I uninstall the app


  @DAT-52471
  Scenario: Install app and validate configuration according to DPK
    Given I have an app entity from "apps/app_service_fields.json"
    And publish the app
    When I install the app
    And I get service by name "hello"
    Then I validate service configuration in dpk is equal to service from app
    And "service" has app scope

  @DAT-54655
  Scenario: Install a valid app
    Given I have an app entity from "apps/app.json"
    And publish the app
    When I install the app
    Then i can create pipeline function node from the app service

  @DAT-68027
  Scenario: Install a valid app with dataset component
    Given I have an app entity from "apps/app_dataset_component.json"
    And publish the app
    When I install the app
    Then The dataset component has been installed successfully