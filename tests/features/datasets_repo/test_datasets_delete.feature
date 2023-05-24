@qa-nightly
Feature: Datasets repository delete service testing

    Background: Initiate Platform Interface and create a project
        Given Platform Interface is initialized as dlp and Environment is set according to git branch
        And I create a project by the name of "datasets_delete"

    @testrail-C4523085
    Scenario: Delete dataset by name
        Given There are no datasets
        And I create a dataset with a random name
        When I delete the dataset that was created by name
        Then Dataset with same name does not exists

    @testrail-C4523085
    Scenario: Delete dataset by id
        Given There are no datasets
        And I create a dataset with a random name
        When I delete the dataset that was created by id
        Then Dataset with same name does not exists

    @testrail-C4523085
    Scenario: Delete a non-existing dataset
        Given There are no datasets
        And I create a dataset with a random name
        When I try to delete a dataset by the name of "Some Dataset Name"
        Then "NotFound" exception should be raised
        And No dataset was deleted

