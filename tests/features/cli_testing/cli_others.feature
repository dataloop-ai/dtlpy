#noinspection CucumberUndefinedStep
Feature: Cli Others

    Background: background
        Given Platform Interface is initialized as dlp and Environment is set according to git branch
        And I am logged in
        And I have context random number

    Scenario: Exit
        When I perform command:
            |exit|
        Then I succeed

    Scenario: Help
        When I perform command:
            |help|
        Then I succeed
        And "CLI for Dataloop" in output
        When I perform command:
            |-h|
        Then I succeed
        And "CLI for Dataloop" in output
        When I perform command:
            |--h|
        Then I succeed
        And "CLI for Dataloop" in output

    Scenario: Exit
        When I perform command:
            |version|
        Then I succeed
        And Version is correct