Feature: Items repository download_batch function testing

    Background: Initiate Platform Interface and create a project
        Given Platform Interface is initialized as dlp and Environment is set to development
        And There is a project by the name of "items_download_batch"
        And I create a dataset by the name of "Dataset"
        And There are "2" Items

    Scenario: Download batch items to buffer
        When I download batched items to buffer
        And I delete all items from host
        Then I can upload items from buffer to host

    Scenario: Download items to local
        When I download items to local path "download_batch"
        Then Items are saved in "download_batch/image"

    Scenario: Finally
        Given Clean up "items_download_batch"