Feature: Test app umbrella refs - App services

  Background: Initialize
    Given Platform Interface is initialized as dlp and Environment is set according to git branch
    And I create a project by the name of "service-app-refs"

  @DAT-72119
  Scenario: Update app with app service - Should update the app service to latest app version
    Given I fetch the dpk from 'apps/app_move_item_service.json' file
    When I publish a dpk
    And I install the app
    And I set code path "move_item" to context
    And I pack directory by name "move_item"
    And I add codebase to dpk
    And I set code path "move_item" to context
    And I pack directory by name "move_item"
    And I add codebase to dpk
    And I publish a dpk
    And I increment app dpk_version
    And I update an app
    And I get service in index "0"
    Then I validate service response params
      | key             | value |
      | packageRevision | 1.0.1 |
    And "service" has app scope
