Feature: Test datasets unlocking method

  Background: Initiate Platform Interface and create a project
    Given Platform Interface is initialized as dlp and Environment is set according to git branch
    And I create a project by the name of "unlocking_tests"

  @DAT-88564
  Scenario: Unlock dataset that is not locked
    When I create a dataset with a random name
    And I unlock a dataset
    Then I receive error with status code "400"
    Then "dataset is not locked" in error message

  @DAT-88566
  Scenario: Unlock successfully locked dataset
    When I create a dataset with a random name
    And There are "100" items
    Given There is an item
    Then I able to rename item to "/testing_name.jpg" while Exporting locked dataset
