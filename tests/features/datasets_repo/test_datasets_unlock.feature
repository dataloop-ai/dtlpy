Feature: Test datasets unlocking method

  Background: Initiate Platform Interface and create a project
    Given Platform Interface is initialized as dlp and Environment is set according to git branch
    And I create a project by the name of "unlocking_tests"
    When I create a dataset with a random name

  @DAT-88564
  Scenario: Unlock dataset that is not locked
    When I unlock a dataset
    Then I receive error with status code "400"
    Then "dataset is not locked" in error message

  @DAT-88566
  Scenario: Unlock successfully locked dataset
    When There are "100" items
    Given There is an item
    Then I able to rename item to "/testing_name.jpg" while Exporting locked dataset

  @DAT-89311
  Scenario: Unlock successfully locked dataset using time out
    When There are "100" items
    And I create "delete_me" folder
    When I export dataset to created folder with lock dataset and export time out "2"
    When I wait "2"
    Then I check if created folder is empty
    When I check dataset is locked
    Then I wait "2"
    Then I check dataset is not locked
    Then I check if created folder is empty
    Then I wait "8"
    Then I check if created folder is not empty
    Then delete the folder and its content
