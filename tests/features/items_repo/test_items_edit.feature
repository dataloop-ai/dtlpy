Feature: Items repository update service testing

    Background: Initiate Platform Interface and create a project
        Given Platform Interface is initialized as dlp and Environment is set according to git branch
        And There is a project by the name of "items_edit"
        And I create a dataset with a random name
        And There is an item

    Scenario: Update items name
        When I update items name to "/test_name.jpg"
        Then I receive an Item object with name "/test_name.jpg"
        And Item in host was changed to "/test_name.jpg"
        And Only name attributes was changed

    Scenario: Update items path
        Given And There is an item by the name of "/test_item.jpg"
        When I update items name to "/folder/test_item.jpg"
        Then I receive an Item object with name "/folder/test_item.jpg"
        And Item in host was changed to "/folder/test_item.jpg"
        And PageEntity has directory item "/folder"

    Scenario: Update item system metadata - with param system_metadata=True
        When I update item system metadata with system_metadata="True"
        Then Then I receive an Item object
        And Item in host has modified metadata
        And Only metadata was changed

    Scenario: Update item system metadata - with param system_metadata=False
        When I update item system metadata with system_metadata="False"
        Then Then I receive an Item object
        And Item in host was not changed

