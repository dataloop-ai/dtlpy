Feature: Datasets repository delete function testing

    Background: Initiate Platform Interface and create a project
        Given Platform Interface is initialized as dlp and Environment is set to development
        And There is a project by the name of "datasets_delete"

    Scenario: Delete dataset by name
        Given There are no datasets
        And I create a dataset with a random name
        When I delete the dataset that was created by name
        Then Dataset with same name does not exists
    
    Scenario: Delete dataset by id
        Given There are no datasets
        And I create a dataset with a random name
        When I delete the dataset that was created by id
        Then Dataset with same name does not exists

    Scenario: Delete a non-existing dataset
        Given There are no datasets
        And I create a dataset with a random name
        When I try to delete a dataset by the name of "Some Dataset Name"
        Then "NotFound" exception should be raised
        And No dataset was deleted

