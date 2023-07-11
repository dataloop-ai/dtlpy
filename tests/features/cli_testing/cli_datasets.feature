#noinspection CucumberUndefinedStep
Feature: Cli Datasets

    Background: background
        Given Platform Interface is initialized as dlp and Environment is set according to git branch
        And I am logged in
        And I have context random number

    @testrail-C4523068
    @DAT-46476
    Scenario: Datasets Create
        When I perform command:
            |projects|create|-p|to-delete-test-<random>_cli_datasets_project|
        Then I succeed
        And I wait "5"
        When I perform command:
            |datasets|create|-p|to-delete-test-<random>_cli_datasets_project|-d|test_<random>_cli_datasets_dataset|
        Then I succeed
        And I create a dataset by the name of "test_<random>_cli_datasets_dataset" in project "to-delete-test-<random>_cli_datasets_project"

    @testrail-C4523068
    @DAT-46476
    Scenario: Datasets list
        When I perform command:
            |datasets|ls|-p|to-delete-test-<random>_cli_datasets_project|
        Then I succeed
        And "test_<random>_cli_datasets_dataset" in output

    @testrail-C4523068
    @DAT-46476
    Scenario: Finally
        Given I delete the project by the name of "to-delete-test-<random>_cli_datasets_project"
        And I clean folder "<rel_path>/cli_dataset_download"
