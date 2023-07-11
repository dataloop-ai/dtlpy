Feature: Items repository upload_batch service testing

    Background: Initiate Platform Interface and create a project
        Given Platform Interface is initialized as dlp and Environment is set according to git branch
        And I create a project by the name of "items_upload_batch"
        And I create a dataset with a random name

    @testrail-C4523121
    @DAT-46542
    Scenario: Upload items from pandas data frame
        When I upload item using data frame from "upload_batch/to_upload"
        And I download items to local path "upload_dataframe/to_compare"
        Then Items in "upload_batch/to_upload" should equal items in "upload_dataframe/to_compare/items"
        And Items should have metadata


