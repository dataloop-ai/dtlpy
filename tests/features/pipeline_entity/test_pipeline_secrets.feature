@bot.create
Feature: Pipeline secrets

  Background: Initiate Platform Interface and create a project
    Given Platform Interface is initialized as dlp and Environment is set according to git branch
    And I create a project by the name of "pipeline_secret"
    And I create a dataset with a random name

  @pipelines.delete
  @DAT-74670
  Scenario: Pipeline secret should saved on the service code node
    Given I create a dataset with a random name
    And I create pipeline with the name "pipeline"
    And I create "code" node with params
      | key      | value |
      | position | (1,1) |
    And I create "key_value" integration with name "pipeline_secret"
    When I add integration to pipeline secrets and update pipeline
    And I add and connect all nodes in list to pipeline entity
    And I install pipeline in context
    And I get service in index "0"
    Then Integration display on service secrets