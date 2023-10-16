Feature: Test datasets clone method

  Background: Initiate Platform Interface and create a project
    Given Platform Interface is initialized as dlp and Environment is set according to git branch
    And I create a project by the name of "clone_dataset"
    And I create a dataset with a random name

  @DAT-53963
  Scenario: Clone dataset to existing dataset using dataset.id
    Given There are "10" items
    When I create another dataset with a random name
    And I call datasets.clone using dataset.id
    Then Cloned dataset has "10" items
