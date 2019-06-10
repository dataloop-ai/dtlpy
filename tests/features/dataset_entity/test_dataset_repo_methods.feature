Feature: Annotation Entity repo functions

    Background: Initiate Platform Interface
        Given Platform Interface is initialized as dlp and Environment is set to development
        And There are no projects
        And There is a project by the name of "Project"
        And I create a dataset by the name of "Dataset"

    Scenario: Download Annotations
        Given Labels in file: "labels.json" are uploaded to test Dataset
        And Item in path "0000000162.jpg" is uploaded to "Dataset"
        And Item is annotated with annotations in file: "0162_annotations.json"
        And There is no folder by the name of "json" in assets folder
        When I download dataset entity annotations to assets
        Then I get a folder named "json" in assets folder
        And Annotations downloaded equal to the annotations uploaded

    Scenario: Download dataset with items
        Given Item in path "0000000162.png" is uploaded to "Dataset"
        And Labels in file: "labels.json" are uploaded to test Dataset
        And Item is annotated with annotations in file: "0162_annotations.json"
        And There are no folder or files in folder "downloaded_dataset"
        When I download dataset entity to "downloaded_dataset"
        Then Dataset downloaded to "downloaded_dataset" is equal to dataset in "downloaded_dataset-should_be"
        And There is no "log" file in folder "downloaded_dataset"

    Scenario: Delete dataset
        When I delete a dataset entity
        Then There are no datasets

    # Scenario: List dataset items
    #     Given There is an item
    #     When I list items in dataset entity
    #     Then I receive a PageEntity object
    #     And PageEntity items has lenght of "1"
    #     And Item in PageEntity items equals item uploaded

    # Scenario: Get an existing item
    #     Given There is an item
    #     When I get the dataset entity item by id
    #     Then I receive an Item object
    #     And The item I received equals the item I uploaded

    # Scenario: Upload items batch
    #     When I upload item batch from "upload_batch/to_upload"
    #     And I download dataset entity items to local path "upload_batch/to_compare"
    #     Then Items in "upload_batch/to_upload" should equal items in "upload_batch/to_compare/image"

    # Scenario: Download items to local
    #     Given There are "2" Items
    #     When I download dataset entity items to local path "download_batch"
    #     Then Items are saved in "download_batch/image"

    # Scenario: Create new recipe
    #     When I create a new recipe to dataset entity
    #     And I update dataset recipe to the new recipe
    #     Then Dataset recipe in host equals the one created

    # Scenario: Upload a single item
    #     When I upload to dataset entity a file in path "0000000162.jpg"
    #     Then Item exist in host
    #     And Upload method returned an Item object
    #     And Item object from host equals item uploaded
    #     And Item in host equals item in "0000000162.jpg"