Feature: Datasets repository download function testing

    Background: Initiate Platform Interface and create a project
        Given Platform Interface is initialized as dlp and Environment is set to development
        And There is a project by the name of "datasets_download"
        And I create a dataset with a random name

    Scenario: Download dataset with items
        Given Item in path "0000000162.png" is uploaded to "Dataset"
        And Labels in file: "labels.json" are uploaded to test Dataset
        And Item is annotated with annotations in file: "0162_annotations.json"
        And There are no folder or files in folder "downloaded_dataset"
        When I download dataset to "downloaded_dataset"
        Then Dataset downloaded to "downloaded_dataset" is equal to dataset in "downloaded_dataset-should_be"
        And There is no "log" file in folder "downloaded_dataset"

    Scenario: Finally
        Given Clean up