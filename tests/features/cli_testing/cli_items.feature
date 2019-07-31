#noinspection CucumberUndefinedStep
Feature: Cli Items

    Background: background
        Given Platform Interface is initialized as dlp and Environment is set to development
        And I am logged in
        And Environment is "dev"
        And I have context random number

    Scenario: Items ls
        When I perform command:
            |projects|create|-p|cli_items_project_<random>|
        And I succeed
        Then I wait "4"
        When I perform command:
            |datasets|create|-p|cli_items_project_<random>|-d|cli_items_dataset_<random>|
        And I succeed
        And I perform command:
            |items|ls|-p|cli_items_project_<random>|-d|cli_items_dataset_<random>|
        Then I succeed

    Scenario: Items upload - maximum params given
        When I perform command:
            |items|upload|-p|cli_items_project_<random>|-d|cli_items_dataset_<random>|-f|<rel_path>/0000000162.jpg|-r|/folder|
        Then I succeed

    Scenario: Items upload - maximum params given
        When I perform command:
            |items|upload|-p|cli_items_project_<random>|-d|cli_items_dataset_<random>|-f|<rel_path>/0000000162.jpg|
        Then I succeed

    Scenario: Finally
        Given I delete the project by the name of "cli_items_project_<random>"