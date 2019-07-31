Feature: Item Entity repo functions

    Background: Initiate Platform Interface
        Given Platform Interface is initialized as dlp and Environment is set to development
        And There is a project by the name of "item_repo_methods"
        And I create a dataset with a random name

    Scenario: Download item
        Given There are no items
        And I upload an item by the name of "/test_item.jpg"
        And Folder "test_download_item_repo_methods" is empty
        When I download an item entity by the name of "/test_item.jpg" to "test_download_item_repo_methods"
        Then There are "1" files in "test_download_item_repo_methods"
        And Item is correctly downloaded to "test_download_item_repo_methods/items/test_item.jpg" (compared with "0000000162.jpg")

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

    Scenario: Move folder with leading slash
        Given There is an item
        When I move item to "/main_dir/sub_dir"
        Then Item in host moved to a new directory

    Scenario: Move folder - no leading slas
        Given There is an item
        When I move item to "main_dir/sub_dir"
        Then Item in host moved to a new directory
    
    Scenario: Move folder - with new name
        Given There is an item
        When I move item to "main_dir/sub_dir/new_name.jpg"
        Then Item in host moved to a new directory

    Scenario: Finally
        Given Clean up