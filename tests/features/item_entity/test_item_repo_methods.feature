Feature: Item Entity repo services

    Background: Initiate Platform Interface
        Given Platform Interface is initialized as dlp and Environment is set according to git branch
        And There is a project by the name of "item_repo_methods"
        And I create a dataset with a random name

    @testrail-C4523123
    Scenario: Download item
        Given There are no items
        And I upload an item by the name of "test_item.jpg"
        And Folder "test_download_item_repo_methods" is empty
        When I download an item entity by the name of "/test_item.jpg" to "test_download_item_repo_methods"
        Then There are "1" files in "test_download_item_repo_methods"
        And Item is correctly downloaded to "test_download_item_repo_methods/test_item.jpg" (compared with "0000000162.jpg")

    @testrail-C4523123
    Scenario: Delete item
        Given There are no items
        And I upload an item by the name of "test_item.jpg"
        When I delete the item
        Then There are no items

    @testrail-C4523123
    Scenario: Update items name
        Given There is an item
        When I update item entity name to "/test_name.jpg"
        Then I receive an Item object with name "/test_name.jpg"
        And Item in host was changed to "/test_name.jpg"
        And Only name attributes was changed

    @testrail-C4523123
    Scenario: To Json - not annotated item
        Given I upload item in path "assets_split/ann_json_to_object/0000000162.jpg" to dataset
        Then Object "Item" to_json() equals to Platform json.

    @testrail-C4523123
    Scenario: To Json - annotated video
        Given I upload item in path "assets_split/ann_json_to_object/sample_video.mp4" to dataset
        When Item is annotated with annotations in file: "assets_split/ann_json_to_object/video_annotations.json"
        Then Item is annotated
        Then Object "Item" to_json() equals to Platform json.

