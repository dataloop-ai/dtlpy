Feature: App service update entities externally

  Background: Initiate Platform Interface and create a project
    Given Platform Interface is initialized as dlp and Environment is set according to git branch
    And I create a project by the name of "app_service_update_entities"
    And I create a dataset with a random name


  @DAT-86672
  Scenario: Update app service sdk version
    Given I fetch the dpk from 'model_dpk/modelsDpks.json' file
    When I add a service to the DPK
    When I publish a dpk to the platform
    When I install the app
    When I update app service SDK version to "1.107.8"
    Then SDK version should be updated to "1.107.8"
    And App custom installation service should be updated to "1.107.8"
