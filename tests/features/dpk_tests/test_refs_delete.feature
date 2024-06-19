Feature: Refs Block delete validation

  Background:
    Given Platform Interface is initialized as dlp and Environment is set according to git branch
    And I create a project by the name of "refs_validation"

  @DAT-71436
  Scenario: Pause pipeline with faas , predict and code nodes - Should be able to delete the node services
    When get global model package
    And I create a model with a random name
    Given model is trained
    And a service
    And a dpk with custom node
    And an app
    And pipeline with model, service, code and custom nodes
    When I install pipeline
    And I pause pipeline in context
    And I pause the app
    Then I Should be able to uninstall service
    And I Should be able to delete model
    And I Should be able to uninstall app
    And I Should be able to delete dpk
