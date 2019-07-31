Feature: Items repository upload_batch function testing

    Background: Initiate Platform Interface and create a project
        Given Platform Interface is initialized as dlp and Environment is set to development
        And There is a project by the name of "items_upload_batch"
        And I create a dataset with a random name

    Scenario: Upload items batch
        When I upload item batch from "upload_batch/to_upload"
        And I download items to local path "upload_batch/to_compare"
        Then Items in "upload_batch/to_upload" should equal items in "upload_batch/to_compare/image"

    Scenario: Finally
        Given Clean up