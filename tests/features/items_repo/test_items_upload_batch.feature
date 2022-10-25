Feature: Items repository upload_batch service testing

    Background: Initiate Platform Interface and create a project
        Given Platform Interface is initialized as dlp and Environment is set according to git branch
        And I create a project by the name of "items_upload_batch"
        And I create a dataset with a random name

    @testrail-C4523120
    Scenario: Upload items batch
        When I upload item batch from "upload_batch/to_upload"
        And I download items to local path "upload_batch/to_compare"
        Then Items in "upload_batch/to_upload" should equal items in "upload_batch/to_compare/image"

