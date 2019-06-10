Feature: Datasets repository create function testing

    Background: Initiate Platform Interface and create a project
        Given Platform Interface is initialized as dlp and Environment is set to development
        And There are no projects
        And There is a project by the name of "Project"

    Scenario: Create a dataset with a legal name
        Given There are no datasets
        When I create a dataset by the name of "Dataset"
        Then Dataset object by the name of "Dataset" should be exist
        And Dataset by the name of "Dataset" should exist in host

    Scenario: Create a dataset with an illegal name
        Given There are no datasets
        When When I try to create a dataset with a blank name
        Then "BadRequest" exception should be raised
        And There are no datasets

    Scenario: Create a dataset with an existing dataset name
        Given There are no datasets
        And I create a dataset by the name of "Dataset"
        When I try to create a dataset by the name of "Dataset"
        Then "BadRequest" exception should be raised
        And No dataset was created