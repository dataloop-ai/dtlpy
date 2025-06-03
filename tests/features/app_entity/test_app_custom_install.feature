Feature: Test Update app custom installation

  Background: Initialize
    Given Platform Interface is initialized as dlp and Environment is set according to git branch
    And I create a project by the name of "custom-installation-create"

  @DAT-94355
  Scenario: Update app custom installation with models - install the full model config
    Given I publish a model dpk from file "model_dpk/dpkWith2Models.json" package "dummymodel" with status "pre-trained"
    When I create a context.custom_installation var
    And I "remove" the "models" "model2" from context.custom_installation
    And I install the app with custom_installation "True"
    And I "add" the "models" "model2" from context.custom_installation
    And I update app custom installation
    And i fetch the model by the name "model2"
    Then model status should be "trained" with execution "False" that has function "None"
