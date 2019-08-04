#noinspection CucumberUndefinedStep
Feature: Cli Datasets

    Background: background
        Given Platform Interface is initialized as dlp and Environment is set to development
        And I am logged in
        And Environment is "dev"
        And I have context random number

    Scenario: Datasets Create
        When I perform command:
            |projects|create|-p|cli_datasets_project_<random>|
        Then I succeed
        And I wait "5"
        When I perform command:
            |datasets|create|-p|cli_datasets_project_<random>|-d|cli_datasets_dataset_<random>|
        Then I succeed
        And There is a dataset by the name of "cli_datasets_dataset_<random>" in project "cli_datasets_project_<random>"
        
    Scenario: Datasets list
        When I perform command:
            |datasets|ls|-p|cli_datasets_project_<random>|
        Then I succeed
        And "cli_datasets_dataset_<random>" in output

    Scenario: Finally
        Given I delete the project by the name of "cli_datasets_project_<random>"
        And I clean folder "<rel_path>/cli_dataset_download"