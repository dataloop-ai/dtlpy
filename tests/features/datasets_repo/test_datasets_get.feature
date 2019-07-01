Feature: Datasets repository get function testing

    Background: Initiate Platform Interface and create a project
        Given Platform Interface is initialized as dlp and Environment is set to development
        And There is a project by the name of "datasets_get"

    Scenario: Get an existing dataset by name
        Given There are no datasets
        And I create a dataset by the name of "Dataset"
        When I get a dataset by the name of "Dataset"
        Then I get a dataset by the name of "Dataset"
        And The dataset I got is equal to the one created

    Scenario: Get an existing project by id
        Given There are no datasets
        And I create a dataset by the name of "Dataset"
        When I get a dataset by the id of the dataset "Dataset"
        Then I get a dataset by the name of "Dataset"
        And The dataset I got is equal to the one created

    Scenario: Get non-existing dataset by name
        Given There are no datasets
        When I try to get a dataset by the name of "Dataset"
        Then "NotFound" exception should be raised

    Scenario: Get non-existing dataset by id
        Given There are no datasets
        When I try to get a dataset by id
        Then "InternalServerError" exception should be raised

    Scenario: Finally
        Given Clean up "datasets_get"