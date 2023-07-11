Feature: Items repository download_batch service testing

    Background: Initiate Platform Interface and create a project
        Given Platform Interface is initialized as dlp and Environment is set according to git branch
        And I create a project by the name of "items_download_batch"
        And I create a dataset with a random name
        And There are "2" Items

    @testrail-C4523114
    @DAT-46535
    Scenario: Download batch items to buffer
        When I download batched items to buffer
        And I delete all items from host
        Then I can upload items from buffer to host

    @testrail-C4523114
    @DAT-46535
    Scenario: Download items to local
        When I download items to local path "download_batch"
        Then Items are saved in "download_batch/image"


