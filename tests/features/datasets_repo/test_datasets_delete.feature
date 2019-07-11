Feature: Datasets repository delete function testing

    Background: Initiate Platform Interface and create a project
        Given Platform Interface is initialized as dlp and Environment is set to development
        And There is a project by the name of "datasets_delete"

    Scenario: Delete dataset by name
        Given There are no datasets
        And I create a dataset by the name of "Dataset"
        When I delete a dataset by the name of "Dataset"
        Then There are no datasets
    
    Scenario: Delete dataset by id
        Given There are no datasets
        And I create a dataset by the name of "Dataset"
        When I delete a dataset by the id of the dataset "Dataset"
        Then There are no datasets

    Scenario: Delete a non-existing dataset
        Given There are no datasets
        And I create a dataset by the name of "Dataset"
        When I try to delete a dataset by the name of "Some Dataset Name"
        Then "NotFound" exception should be raised
        And No dataset was deleted

    Scenario: Finally
        Given Clean up