#noinspection CucumberUndefinedStep
Feature: Cli Projects

    Background: background
        Given Platform Interface is initialized as dlp and Environment is set according to git branch
        And I am logged in
        And I have context random number

    Scenario: Projects list
        When I perform command:
            |projects|ls|
        Then I succeed

    Scenario: Projects Create
        When I perform command:
            |projects|create|-p|test_<random>_cli_project|
        Then I succeed
        And There is a project by the name of "test_<random>_cli_project"
        And "test_<random>_cli_project" in output

    Scenario: Finally
        Given I delete the project by the name of "test_<random>_cli_project"