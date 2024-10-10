
Feature: plan creation

  Background: Initiate Platform Interface
    Given Platform Interface is initialized as dlp and Environment is set according to git branch

  @DAT-53898
  Scenario: Validate monthly free plan on ORG creation
    When I log in as a "superuser"
    When I create "org" name "free_plan"
    Then Validate plan "Type" is "Free"
    Then Validate plan "Period" is "monthly"

