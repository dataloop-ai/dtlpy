#noinspection CucumberUndefinedStep
Feature: Cli Api

    Background: background
        Given Platform Interface is initialized as dlp and Environment is set to development
        And I am logged in
        And Environment is "dev"
        And I have context random number

    Scenario: Api info
        When I perform command:
            |api|info|
        Then I succeed
        And "environment" in output
        And "token" in output
    
    Scenario: Api info
        When I perform command:
            |api|setenv|-e|local|
        Then I succeed
        And "Platform environment: https://localhost:8443/api/v1" in output

    Scenario: Api info
        When I perform command:
            |api|setenv|-e|dev|
        Then I succeed
        And "Platform environment: https://dev-gate.dataloop.ai/api/v1" in output

    Scenario: Api info
        When I perform command:
            |api|setenv|-e|some_env|
        Then I dont succeed