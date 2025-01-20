Feature: DPK single Id

  Background:
    Given Platform Interface is initialized as dlp and Environment is set according to git branch
    And I create a project by the name of "model_updated_dpk"


  @DAT-70420
  Scenario: DPK - Models > Update dpk codebase and update app - Model should point to new dpk version and service updated
    Given I publish a model dpk from file "model_dpk/modelsDpks.json" package "dummymodel" with status "trained"
    When I install the app
    And I get the dpk by name
    And I set code path "packages_get" to context
    And I pack directory by name "packages_get"
    And I add codebase to dpk
    And I publish a dpk
    And I increment app dpk_version
    And I update an app
    And i fetch the model by the name "test-model"
    And I "deploy" the model
    Then I validate service response params
      | key             | value |
      | packageRevision | 1.0.1 |
    And "model" has app scope
    And I clean the project


  @DAT-71180
  Scenario: DPK - Models > Update dpk model labels and update app - Model labels should not updated
    Given I publish a model dpk from file "model_dpk/modelsDpks.json" package "dummymodel"
    When I install the app without custom_installation
    And I get the dpk by name
    And I remove attributes "labels" from dpk model in index "0"
    And I add att 'labels=["1"]' to dpk 'model' in index '0'
    And I publish a dpk
    And I increment app dpk_version
    And I update an app
    When i fetch the model by the name "test-model"
    Then "model" has app scope
    Then I validate the context.model has the attribute "labels" with value "['0', '1', '2', '3', '4', '5', '6', '7', '8', '9']"
    And I clean the project

