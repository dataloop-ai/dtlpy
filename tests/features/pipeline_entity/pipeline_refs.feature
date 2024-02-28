Feature: Test pipeline refs

  Background: Initiate Platform Interface and create a project
    Given Platform Interface is initialized as dlp and Environment is set according to git branch
    And I create a project by the name of "pipeline-refs"

  @DAT-64799
  Scenario: Test full pipeline refs + cleanup
    When get global model package
    And I create a model with a random name
    Given model is trained
    And a service
    And a dpk with custom node
    And an app
    And pipeline with model, service, code and custom nodes
    When I install pipeline
    Then service should have pipeline refs
    And model should have pipeline refs
    And code node package should have pipeline refs
    And code node service should have pipeline refs
    And app should have pipeline refs
    And dpk should have pipeline refs
    When I delete pipeline
    Then service should not have pipeline refs
    And model should not have pipeline refs
    And app should not have pipeline refs
    And dpk should not have pipeline refs
