@bot.create
Feature: Pipeline code node testing

  Background: Initiate Platform Interface and create a project
    Given Platform Interface is initialized as dlp and Environment is set according to git branch
    And I create a project by the name of "code_node"
    And I create a dataset with a random name

  @pipelines.delete
  @DAT-51870
  Scenario: Pipeline - Update code node name and install - should installed successfully
    Given I create pipeline with the name "pipeline"
    And I create "code" node with params
      | key      | value |
      | position | (1,1) |
    When I add and connect all nodes in list to pipeline entity
    And I install pipeline in context
    And I pause pipeline in context
    And I update pipeline attributes with params
      | key                      | value  |
      | nodes[0].outputs[0].name | item_1 |
    And I get pipeline in context by id
    Then I validate pipeline attributes with params
      | key                      | value  |
      | nodes[0].outputs[0].name | item_1 |
    When I install pipeline in context
    Then Pipeline status is "Installed"