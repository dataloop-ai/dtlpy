#noinspection CucumberUndefinedStep
Feature: Cli Datasets

    Background: background
        Given Platform Interface is initialized as dlp and Environment is set to development
        And I am logged in
        And Environment is "dev"
        And I have context random number

    Scenario: Datasets Create
        When I perform command:
            |projects|create|-p|test_<random>_cli_datasets_project|
        Then I succeed
        And I wait "5"
        When I perform command:
            |datasets|create|-p|test_<random>_cli_datasets_project|-d|test_<random>_cli_datasets_dataset|
        Then I succeed
        And There is a dataset by the name of "test_<random>_cli_datasets_dataset" in project "test_<random>_cli_datasets_project"
        
    Scenario: Datasets list
        When I perform command:
            |datasets|ls|-p|test_<random>_cli_datasets_project|
        Then I succeed
        And "test_<random>_cli_datasets_dataset" in output

    Scenario: Finally
        Given I delete the project by the name of "test_<random>_cli_datasets_project"
        And I clean folder "<rel_path>/cli_dataset_download"