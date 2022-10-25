Feature: Items repository upload service testing

    Background: Initiate Platform Interface and create a project
        Given Platform Interface is initialized as dlp and Environment is set according to git branch
        And I create a project by the name of "items_upload"
        And I create a dataset with a random name

    @testrail-C4523119
    Scenario: Upload a single item
        When I upload a file in path "assets_split/items_upload/0000000162.jpg"
        Then Item exist in host
        And Upload method returned an Item object
        And Item object from host equals item uploaded
        And Item in host when downloaded to "test_items_upload_downloaded_item" equals item in "assets_split/items_upload/0000000162.jpg"

    @testrail-C4523119
    Scenario: Upload a single item to a specific remote path
        When I upload file in path "assets_split/items_upload/0000000162.jpg" to remote path "/folder"
        Then Item exist in host
        And Item in host is in folder "/folder"
        And Upload method returned an Item object
        And Item object from host equals item uploaded
        And Item in host when downloaded to "test_items_upload_downloaded_item" equals item in "assets_split/items_upload/0000000162.jpg"

    @testrail-C4523119
    Scenario: Upload a single item with a specific remote name set via the buffer interface
        When I upload file in path "assets_split/items_upload/0000000162.jpg" with remote name "file.jpg" set via the buffer interface
        Then Item exist in host
        And Item in host has name "file.jpg"
        And Upload method returned an Item object
        And Item object from host equals item uploaded
        And Item in host when downloaded to "test_items_upload_downloaded_item" equals item in "assets_split/items_upload/0000000162.jpg"

    @testrail-C4523119
    Scenario: Upload a single item with a specific remote name
        When I upload the file in path "assets_split/items_upload/0000000162.jpg" with remote name "file.jpg"
        Then Item exist in host
        And Item in host has name "file.jpg"
        And Upload method returned an Item object
        And Item object from host equals item uploaded
        And Item in host when downloaded to "test_items_upload_downloaded_item" equals item in "assets_split/items_upload/0000000162.jpg"

    @testrail-C4523119
    Scenario: Upload a single item with a specific remote name to a specific remote path
        When I upload the file from path "assets_split/items_upload/0000000162.jpg" with remote name "file.jpg" to remote path "/folder"
        Then Item exist in host
        And Item in host is in folder "/folder"
        And Item in host has name "file.jpg"
        And Upload method returned an Item object
        And Item object from host equals item uploaded
        And Item in host when downloaded to "test_items_upload_downloaded_item" equals item in "assets_split/items_upload/0000000162.jpg"

    @testrail-C4523119
    Scenario: Upload a single item - overwrite
        Given Item in path "assets_split/items_upload/0000000162.jpg" is uploaded to "Dataset"
        When I upload with "overwrite" a file in path "assets_split/items_upload/0000000162.jpg"
        Then Item exist in host
        And Upload method returned an Item object
        And Item object from host equals item uploaded
        And Item in host when downloaded to "test_items_upload_downloaded_item" equals item in "assets_split/items_upload/0000000162.jpg"

    @testrail-C4523119
    Scenario: Upload a single item - merge
        Given Item in path "assets_split/items_upload/0000000162.jpg" is uploaded to "Dataset"
        When I upload with "merge" a file in path "assets_split/items_upload/0000000162.jpg"
        Then Item exist in host
        And Upload method returned an Item object
        And Item object from host equals item uploaded
        And Item in host when downloaded to "test_items_upload_downloaded_item" equals item in "assets_split/items_upload/0000000162.jpg"
        And Item was merged to host

#    ToDo - remove - this is no longer forbidden
#    Scenario: Upload an item with an illegal name
#        When I try to upload file in path "assets_split/items_upload/0000000162.jpg" to remote path "/fol.der"
#        Then Number of error files should be larger by one

    @testrail-C4523119
    Scenario: Upload a non-existing file
        When I try to upload file in path "non-existing-path/file.jpg"
        Then "NotFound" exception should be raised

    @testrail-C4523119
    Scenario: Upload items from buffer
        Given There are "3" items
        And I download items to buffer
        And I delete all items from host
        When I upload items from buffer to host
        Then There are "3" items in host

    @testrail-C4523119
    Scenario: Upload item from buffer with specific remote name
        When I use a buffer to upload the file in path "assets_split/items_upload/0000000162.jpg" with remote name "file.jpg"
        Then Item exist in host
        And Item in host has name "file.jpg"
        And Upload method returned an Item object
        And Item object from host equals item uploaded
        And Item in host when downloaded to "test_items_upload_downloaded_item" equals item in "assets_split/items_upload/0000000162.jpg"

#     # TODO - add tests for upload with remote name: url, link, multiview, similarity
#     Scenario: Upload item from URL with specific remote name
#         When I upload a file from a URL "http://some.domain/some_file.png" with remote name "file.png"
#         Then Item exist in host
#         And Item in host has name "file.jpg"
#         And Upload method returned an Item object
#         And Item object from host equals item uploaded

    @testrail-C4523119
    Scenario: Upload a single item with description
        When I upload the file in path "assets_split/items_upload/0000000162.jpg" with description "description"
        Then Item exist in host
        And Upload method returned an Item object
        And Item object from host equals item uploaded
        And Item in host when downloaded to "test_items_upload_downloaded_item" equals item in "assets_split/items_upload/0000000162.jpg"
        And I validate item.description has "description" value