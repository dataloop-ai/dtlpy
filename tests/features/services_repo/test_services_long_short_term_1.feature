Feature: Test service mode update 1
  Background: Initiate Platform Interface and create a project
    Given Platform Interface is initialized as dlp and Environment is set according to git branch
    And I create a project by the name of "service-long-short-term"
    And I create a dataset with a random name
    And I upload item in "0000000162.jpg" to dataset

  @DAT-68557
  Scenario: Updating service from long-term to short term multiple times
    Given I have a paused "short-term" service with concurrency "5"
    And I run "100" executions and activate the service
    When I update the service back and forth "4" times from long-term to short-term
    And I expect all executions to be successful and no execution should have ran twice