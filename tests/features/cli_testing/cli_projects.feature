#noinspection CucumberUndefinedStep
Feature: Cli Projects

    Background: background
        Given Platform Interface is initialized as dlp and Environment is set to development
        And I am logged in
        And Environment is "dev"
        And I have context random number

    Scenario: Projects list
        When I perform command:
            |projects|ls|
        Then I succeed

    Scenario: Projects Create
        When I perform command:
            |projects|create|-p|cli_project_<random>|
        Then I succeed
        And There is a project by the name of "cli_project_<random>"
        And "cli_project_<random>" in output

    Scenario: Finally
        Given I delete the project by the name of "cli_project_<random>"