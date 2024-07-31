Feature: Test app umbrella refs - Auto update Pipeline nodes

  Background: Initialize
    Given Platform Interface is initialized as dlp and Environment is set according to git branch
    And I create a project by the name of "auto-update-refs"

  @DAT-72549
  @DAT-72923
  Scenario: Auto update app model service
    Given I publish a model dpk from file "model_dpk/basicModelDpk.json" package "dummymodel" with status "trained"
    When I install the app without custom_installation
    And I update app auto update to "True"
    And I get last model in project
    And I "deploy" the model
    And I get the dpk by name
    And i update dpk compute config "default" runtime "runnerImage" to "jjanzic"
    And I publish a dpk
    And I wait for app version to be updated according to dpk version
    And I get last model in project
    And I get service in index "-1"
    Then I validate service response params
      | key             | value |
      | packageRevision | 1.0.1 |
    And "model" has app scope
    And "service" has app scope
    And service runnerImage is "jjanzic"
    And model status should be "deployed" with execution "False" that has function "None"
