Feature: Items repository upload service testing

    Background: Initiate Platform Interface and create a project
        Given Platform Interface is initialized as dlp and Environment is set according to git branch
        And There is a project by the name of "items_upload"
        And I create a dataset with a random name

    Scenario: Upload a single item
        When I upload a file in path "assets_split/items_upload/0000000162.jpg"
        Then Item exist in host
        And Upload method returned an Item object
        And Item object from host equals item uploaded
        And Item in host when downloaded to "test_items_upload_downloaded_item" equals item in "assets_split/items_upload/0000000162.jpg"

    Scenario: Upload a single item to a specific remote path
        When I upload file in path "assets_split/items_upload/0000000162.jpg" to remote path "/folder"
        Then Item exist in host
        And Item in host is in folder "/folder"
        And Upload method returned an Item object
        And Item object from host equals item uploaded
        And Item in host when downloaded to "test_items_upload_downloaded_item" equals item in "assets_split/items_upload/0000000162.jpg"
    
    Scenario: Upload a single item with a specific remote name
        When I upload the file in path "assets_split/items_upload/0000000162.jpg" with remote name "file.jpg"
        Then Item exist in host
        And Item in host has name "file.jpg"
        And Upload method returned an Item object
        And Item object from host equals item uploaded
        And Item in host when downloaded to "test_items_upload_downloaded_item" equals item in "assets_split/items_upload/0000000162.jpg"

    Scenario: Upload a single item - overwrite
        Given Item in path "assets_split/items_upload/0000000162.jpg" is uploaded to "Dataset"
        When I upload with "overwrite" a file in path "assets_split/items_upload/0000000162.jpg"
        Then Item exist in host
        And Upload method returned an Item object
        And Item object from host equals item uploaded
        And Item in host when downloaded to "test_items_upload_downloaded_item" equals item in "assets_split/items_upload/0000000162.jpg"
        #Todo
        # And Item was overwrite to host

    Scenario: Upload a single item - merge
        Given Item in path "assets_split/items_upload/0000000162.jpg" is uploaded to "Dataset"
        When I upload with "merge" a file in path "assets_split/items_upload/0000000162.jpg"
        Then Item exist in host
        And Upload method returned an Item object
        And Item object from host equals item uploaded
        And Item in host when downloaded to "test_items_upload_downloaded_item" equals item in "assets_split/items_upload/0000000162.jpg"
        And Item was merged to host

    Scenario: Upload an item with an illegal name
        When I try to upload file in path "assets_split/items_upload/0000000162.jpg" to remote path "/fol.der"
        Then Number of error files should be larger by one

    Scenario: Upload a non-existing file
        When I try to upload file in path "non-existing-path/file.jpg"
        Then "NotFound" exception should be raised

    Scenario: Upload items from buffer
        Given There are "3" items
        And I download items to buffer
        And I delete all items from host
        When I upload items from buffer to host
        Then There are "3" items in host

    Scenario: Upload a single item - video
        When I upload a file in path "sample_video.mp4"
        Then Item exist in host
        And Upload method returned an Item object
        And Item object from host equals item uploaded
        #todo
        # And vidoe download from host equal video in "sample_video.mp4"

