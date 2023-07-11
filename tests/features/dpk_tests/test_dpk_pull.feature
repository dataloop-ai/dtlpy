Feature: Pull Dpk
  Background:
    Given Platform Interface is initialized as dlp and Environment is set according to git branch
    And I create a project by the name of "Project_test_app_get"
    And I fetch the dpk from 'apps/app.json' file
    And I publish a dpk to the platform

  @testrail-C4524925
  @DAT-46515
  Scenario: I pull the dpk
    When I pull the dpk
    Then I should have a dpk file
