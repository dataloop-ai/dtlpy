Feature: Dataset SDK

    Background: Initiate Platform Interface and create a project
        Given Platform Interface is initialized as dlp and Environment is set according to git branch
        And I create a project by the name of "my-project-dataset"
        And Create a Dataset "my-dataset-name"


    @testrail-C4523097
    @DAT-46508
    Scenario: Dataset SDK Scenario
        When Get Commands - Get Projects Datasets List
        Then Get Dataset by Name
        And Get a dataset by ID
        And Print a Dataset

    @testrail-C4523097
    @DAT-46508
    Scenario: Create and Manage Datasets
        When Clone Dataset "clone-dataset"
        And I upload a file in path "assets_split/items_upload/0000000162.jpg"
        And I clone an item
        Then Merge Datasets "merge-dataset"
