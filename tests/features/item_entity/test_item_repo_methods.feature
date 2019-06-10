Feature: Item Entity repo functions

    Background: Initiate Platform Interface
        Given Platform Interface is initialized as dlp and Environment is set to development
        And There are no projects
        And There is a project by the name of "Project"
        And I create a dataset by the name of "Dataset"

    Scenario: Download item
        Given There are no items
        And I upload an item by the name of "/test_item.jpg"
        And Folder "download_item" is empty
        When I download an item entity by the name of "/test_item.jpg" to "download_item"
        Then There are "1" files in "download_item"
        And Item is correctlly downloaded to "download_item/image/test_item.jpg" (compared with "0000000162.jpg")

    Scenario: Delete item
        Given There are no items
        And I upload an item by the name of "/test_item.jpg"
        When I delete the item
        Then There are no items

    Scenario: Update items name
        Given There is an item
        When I update item entity name to "/test_name.jpg"
        Then I receive an Item object with name "/test_name.jpg"
        And Item in host was changed to "/test_name.jpg"
        And Only name attributes was changed

    # Scenario: List all items annotations
    #     Given There is an item
    #     And Labels in file: "labels.json" are uploaded to test Dataset
    #     And Item is annotated with annotations in file: "0162_annotations.json"
    #     When I list all item entity annotations
    #     Then I receive a list of all annotations
    #     And The annotations in the list equals the annotations uploaded

    # Scenario: Get an existing annotation by id
    #     Given There is an item
    #     And Labels in file: "labels.json" are uploaded to test Dataset
    #     And Item is annotated with annotations in file: "0162_annotations.json"
    #     And There is annotation x
    #     When I get the item entity annotation by id
    #     Then I receive an Annotation object
    #     And Annotation received equals to annotation x

    # Scenario: Uploade annotations from file
    #     Given There is an item
    #     And Labels in file: "labels.json" are uploaded to test Dataset
    #     When I uploade to item entity annotations from file: "0162_annotations.json"
    #     Then Item should have annotations uploaded