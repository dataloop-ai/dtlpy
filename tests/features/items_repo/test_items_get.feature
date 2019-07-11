Feature: Items repository get function testing

    Background: Initiate Platform Interface and create a project
        Given Platform Interface is initialized as dlp and Environment is set to development
        And There is a project by the name of "items_get"
        And I create a dataset by the name of "Dataset"

    Scenario: Get an existing item by id
        Given There is an item
        When I get the item by id
        Then I receive an Item object
        And The item I received equals the item I uploaded

    Scenario: Get an non-existing item by id
        When I try to get item by "some_id"
        Then "NotFound" exception should be raised

    Scenario: Get an existing item by remote path
        Given There is an item
        When I get the item by remote path "/0000000162.jpg"
        Then I receive an Item object
        And The item I received equals the item I uploaded

    Scenario: Get a non-existing item by remote path
        When I try to get an item by remote path "/some_path"
        Then "NotFound" exception should be raised

    Scenario: Use get function with neither filename or remote path
        When I try to use get functions with no params
        Then "BadRequest" exception should be raised

    Scenario: Get an existing item by filename when 2 files with the same name exist
        Given There are 2 items by the name of "0000000162.jpg"
        When I try to get an item by remote path "**/0000000162.jpg"
        Then "NotFound" exception should be raised
    
    Scenario: Finally
        Given Clean up