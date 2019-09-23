Feature: Datasets repository list function testing

    Background: Initiate Platform Interface and create a project
        Given Platform Interface is initialized as dlp and Environment is set to development
        And There is a project by the name of "datasets_list"

    Scenario: List all datasets when no dataset exists
        Given There are no datasets
        When I list all datasets
        Then I receive an empty datasets list

    Scenario: List all datasets when datasets exist
        Given There are no datasets
        And I careat a dataset by the name of "Dataset"
        When I list all datasets
        Then I receive a datasets list of "1" dataset
        And The dataset in the list equals the dataset I created

