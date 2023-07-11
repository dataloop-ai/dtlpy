Feature: Datasets repository get service testing

    Background: Initiate Platform Interface and create a project
        Given Platform Interface is initialized as dlp and Environment is set according to git branch
        And I create a project by the name of "datasets_get"

    @testrail-C4523088
    @DAT-46496
    Scenario: Get an existing dataset by name
        Given There are no datasets
        And I create a dataset with a random name
        When I get a dataset with the created name
        Then I get a dataset with the created name
        And The dataset I got is equal to the one created

    @testrail-C4523088
    @DAT-46496
    Scenario: Get an existing project by id
        Given There are no datasets
        And I create a dataset with a random name
        When I get a dataset by the id of the dataset "Dataset"
        Then I get a dataset with the created name
        And The dataset I got is equal to the one created

    @testrail-C4523088
    @DAT-46496
    Scenario: Get non-existing dataset by name
        Given There are no datasets
        When I try to get a dataset by the name of "Dataset"
        Then "NotFound" exception should be raised

    @testrail-C4523088
    @DAT-46496
    Scenario: Get non-existing dataset by id
        Given There are no datasets
        When I try to get a dataset by id
        Then "NotFound" exception should be raised


