Feature: Installing apps several times should not create more than one bot

  Background: Initialize
    Given Platform Interface is initialized as dlp and Environment is set according to git branch
    And I create a project by the name of "test_app_bot_creation"

  @DAT-66254
  Scenario: Installing apps several times should not create more than one bot
    Given I have an app entity from "apps/app.json"
    And publish the app
    When I install the app
    Then I should get the app with the same id
    Then The project have only one bot
    When I uninstall the app
    Then The app shouldn't be in listed
    When I install the app
    Then I should get the app with the same id
    Then The project have only one bot