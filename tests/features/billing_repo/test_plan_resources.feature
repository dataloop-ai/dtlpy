Feature: Test Plan Resources

  Background: Initiate Platform Interface
    Given Platform Interface is initialized as dlp and Environment is set according to git branch

  @DAT-53900
  Scenario: Validate given plan has expected resources


    Given I fetch "plans_resources.json" file from "billing"
    Given I get plans resources json
    Then I validate "Free" plan resources
    Then I validate "Basic" plan resources
    Then I validate "Standard" plan resources
    Then I validate "Pro" plan resources
    Then I validate "Pro Plus" plan resources