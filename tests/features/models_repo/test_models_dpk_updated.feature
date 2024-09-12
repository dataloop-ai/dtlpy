Feature: Test model created from dpk with updated app version

  Background:
    Given Platform Interface is initialized as dlp and Environment is set according to git branch
    And I create a project by the name of "model_service_updated"


  @DAT-72492
  Scenario: Update dpk and app version with customInstallation - Shouldn't create new model and
    Given I publish a model dpk from file "model_dpk/modelsDpks.json" package "dummymodel" with status "created"
    When I get the dpk by name
    And I create a context.custom_installation var
    And I install the app with custom_installation "True"
    And I update app auto update to "True"
    And I publish a dpk
    And I wait for app version to be updated according to dpk version
    Then I expect to get "1" models in project

  @DAT-72492
  Scenario: Update dpk and app version without customInstallation - Shouldn't create new model
    Given There are no models in project
    And I publish a model dpk from file "model_dpk/modelsDpks.json" package "dummymodel" with status "created"
    When I get the dpk by name
    And I create a context.custom_installation var
    And I install the app with custom_installation "False"
    And I update app auto update to "True"
    And I publish a dpk
    And I wait for app version to be updated according to dpk version
    Then I expect to get "1" models in project

  @DAT-77777
  Scenario: Model with generated string - Publish new dpk version - Should not create new model
    Given There are no models in project
    And I publish a model dpk from file "model_dpk/modelsDpks.json" package "dummymodel" with status "created"
    When I install the app
    Given I publish a model dpk from file "model_dpk/modelsDpks.json" package "dummymodel" with status "created"
    When I install the app
    And I get the dpk by name
    And I get last model in project
    And I update app auto update to "True"
    Then The model name not changed
    When I publish a dpk
    And I wait for app version to be updated according to dpk version
    Then I expect to get "2" models in project