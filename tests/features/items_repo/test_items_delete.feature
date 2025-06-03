@qa-nightly
Feature: Items repository delete service testing

    Background: Initiate Platform Interface and create a project
        Given Platform Interface is initialized as dlp and Environment is set according to git branch
        And I create a project by the name of "items_delete"
        And I create a dataset with a random name

    @testrail-C4523111
    @DAT-46532
    Scenario: Delete item by name
        Given There are no items
        And I upload an item by the name of "test_item.jpg"
        When I delete the item by name
        Then There are no items

    @testrail-C4523111
    @DAT-46532
    Scenario: Delete item by id
        Given There are no items
        And I upload an item by the name of "test_item.jpg"
        When I delete the item by id
        Then There are no items

    @testrail-C4523111
    @DAT-46532
    Scenario: Delete a non-existing item by name
        Given There are no items
        And I upload an item by the name of "test_item.jpg"
        When I try to delete an item by the name of "Some_item_name"
        Then "NotFound" exception should be raised
        And No item was deleted

    @testrail-C4523111
    @DAT-46532
    Scenario: Delete a non-existing item by id
        Given There are no items
        And I upload an item by the name of "test_item.jpg"
        When I try to delete an item by the id of "Some_id"
        Then "BadRequest" exception should be raised
        And No item was deleted

    @skip_test
    @DAT-93945
    @DM-cache
    Scenario: Delete item by name with cache
        Given There are no items
        And I upload an item by the name of "test_item.jpg"
        When I get the item by id
        And I wait "1"
        When I get the item by id
        When I delete the item by name
        Then There are no items
