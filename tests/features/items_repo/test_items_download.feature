Feature: Items repository download function testing

    Background: Initiate Platform Interface and create a project
        Given Platform Interface is initialized as dlp and Environment is set to development
        And There are no projects
        And There is a project by the name of "Project"
        And I create a dataset by the name of "Dataset"

    Scenario: Download item by name - save locally
        Given There are no items
        And I upload an item by the name of "/test_item.jpg"
        And Folder "download_item" is empty
        When I download an item by the name of "/test_item.jpg" to "download_item"
        Then There are "1" files in "download_item"
        And Item is correctlly downloaded to "download_item/image/test_item.jpg" (compared with "0000000162.jpg")

    Scenario: Download item by id - save locally
        Given There are no items
        And I upload an item by the name of "/test_item.jpg"
        And Folder "download_item" is empty
        When I download an item by the id of "/test_item.jpg" to "download_item"
        Then There are "1" files in "download_item"
        And Item is correctlly downloaded to "download_item/image/test_item.jpg" (compared with "0000000162.jpg")

    Scenario: Download item by id - do not save locally
        Given There are no items
        And I upload an item by the name of "/test_item.jpg"
        When I download without saving an item by the id of "/test_item.jpg"
        Then I receive item data
        When I upload item data by name of "/test_item2.jpg"
        Then Item uploaded from data equals initial item uploaded
    