Feature: Dataset Entity repo services

    Background: Initiate Platform Interface
        Given Platform Interface is initialized as dlp and Environment is set according to git branch
        And I create a project by the name of "dataset_repo_methods"
        And I create a dataset with a random name

    @testrail-C4523094
    @DAT-46505
    Scenario: Download Annotations
        Given Labels in file: "labels.json" are uploaded to test Dataset
        And Item in path "0000000162.jpg" is uploaded to "Dataset"
        And Item is annotated with annotations in file: "0162_annotations.json"
        And There is no folder by the name of "json" in assets folder
        When I download dataset entity annotations to assets
        Then I get a folder named "json" in assets folder
        And Annotations downloaded equal to the annotations uploaded

    @testrail-C4523094
    @DAT-46505
    Scenario: Download dataset with items
        Given Item in path "0000000162.png" is uploaded to "Dataset"
        And Labels in file: "labels.json" are uploaded to test Dataset
        And Item is annotated with annotations in file: "0162_annotations.json"
        And There are no folder or files in folder "downloaded_dataset"
        When I download dataset entity to "downloaded_dataset"
        Then Dataset downloaded to "downloaded_dataset" is equal to dataset in "downloaded_dataset-should_be"
        And There is no "log" file in folder "downloaded_dataset"

    @testrail-C4523094
    @DAT-46505
    Scenario: Delete dataset
        When I delete a dataset entity
        Then Dataset with same name does not exists

    @testrail-C4523094
    @DAT-46505
    Scenario: To Json
        Then Object "Dataset" to_json() equals to Platform json.


    @DAT-68486
    Scenario: unsearchablePaths
        When "add" unsearchable paths "metadata.test" to dataset
        Then "metadata.test" is "added" to dataset schema
        When "delete" unsearchable paths "metadata.test" to dataset
        Then "metadata.test" is "deleted" to dataset schema




