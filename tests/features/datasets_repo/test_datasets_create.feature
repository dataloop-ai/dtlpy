Feature: Datasets repository create function testing

    Background: Initiate Platform Interface and create a project
        Given Platform Interface is initialized as dlp and Environment is set to development
        And There is a project by the name of "datasets_create"

    Scenario: Create a dataset with a legal name
        Given There are no datasets
        When I create a dataset with a random name
        Then Dataset object with the same name should be exist
        And Dataset object with the same name should be exist in host

    # bug in platform dataset is created
    # Scenario: Create a dataset with an illegal name
    #     Given There are no datasets
    #     When When I try to create a dataset with a blank name
    #     Then "BadRequest" exception should be raised
    #     And There are no datasets

    Scenario: Create a dataset with an existing dataset name
        Given There are no datasets
        And I create a dataset with a random name
        When I try to create a dataset by the same name
        Then "BadRequest" exception should be raised
        And No dataset was created

