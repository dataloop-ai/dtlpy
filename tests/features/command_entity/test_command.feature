Feature: command Entity repo - test using dataset clone feature

  Background: Initiate Platform Interface and create a project
    Given Platform Interface is initialized as dlp and Environment is set according to git branch
    And I create a project by the name of "command_test"
    And I create a dataset with a random name

  @testrail-C4523079
  @DAT-46487
  Scenario: Use command with clone dataset
    Given There are "10" items
    When Dataset is cloning
    Then Cloned dataset has "10" items

  @testrail-C4523079
  @DAT-46487
  Scenario: command error  with clone dataset with same name
    When Dataset is cloning with same name get already exist error


  @testrail-C4523079
  @DAT-46487
  Scenario: Use command with clone dataset to existing dataset
    Given There are "10" items
    When I create another dataset with a random name
    And Dataset is cloning to existing dataset
    Then Cloned dataset has "10" items

  @DAT-53962
  Scenario: Use command with clone dataset to existing dataset with filter
    Given There are "11" items
    When I create another dataset with a random name
    And I create filters
    And I add field "filename" with values "/file1*" and operator "None"
    And Dataset is cloning to existing dataset
    Then Cloned dataset has "2" items