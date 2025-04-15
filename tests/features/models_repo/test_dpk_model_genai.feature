Feature: Test dpk with gen model

  Background: Initialize
    Given Platform Interface is initialized as dlp and Environment is set according to git branch
    And I create a project by the name of "dpk-gen-model"

  @DAT-73514
  @models.delete
  Scenario: Create gen model with LLM
    Given I publish a model dpk from file "model_dpk/basicModelDpkGen.json" package "dummymodel" with status "trained"
    When I install the app without custom_installation
    And I get last model in project
    And "model" has app scope
    And model should be with mltype "LLM"

  @DAT-73514
  Scenario: Auto update app model should be LLM
    Given I publish a model dpk from file "model_dpk/basicModelDpk.json" package "dummymodel" with status "trained" and docker image "jjanzic/docker-python3-opencv"
    When I install the app without custom_installation
    And I update app auto update to "True"
    And I get last model in project
    And I "deploy" the model
    And I get the dpk by name
    And i update dpk attribute "Gen AI" to "LLM"
    And I publish a dpk
    And I wait for app version to be updated according to dpk version
    And I get last model in project
    And I get service in index "-1"
    Then I validate service response params
      | key             | value |
      | packageRevision | 1.0.1 |
    And "model" has app scope
    And "service" has app scope
    And service runnerImage is "jjanzic/docker-python3-opencv"
    And model status should be "deployed" with execution "False" that has function "None"
    And model should be with mltype "LLM"



