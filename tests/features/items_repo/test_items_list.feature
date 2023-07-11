@qa-nightly
Feature: Items repository list service testing

    Background: Initiate Platform Interface and create a project
        Given Platform Interface is initialized as dlp and Environment is set according to git branch
        And I create a project by the name of "items_list"
        And I create a dataset with a random name

    @testrail-C4523117
    @DAT-46538
    Scenario: List dataset items
        Given There is an item
        When I list items
        Then I receive a PageEntity object
        And PageEntity items has length of "1"
        And Item in PageEntity items equals item uploaded

    @testrail-C4523117
    @DAT-46538
    Scenario: List dataset items - with size
        Given There are "10" items
        When I list items with size of "5"
        Then I receive a PageEntity object
        And PageEntity items has length of "5"
        And PageEntity items has next page
        And PageEntity next page items has length of "5"
        And PageEntity items does not have next page

    @testrail-C4523117
    @DAT-46538
    Scenario: List dataset items - with offset
        Given There are "10" items
        When I list items with offset of "1" and size of "5"
        Then I receive a PageEntity object
        And PageEntity items has length of "5"
        And PageEntity items does not have next page

    @testrail-C4523117
    @DAT-46538
    Scenario: List dataset items - with query - filename
        Given There are "10" items
        And There is one item by the name of "test_name.jpg"
        When I list items with query filename="/test_name.jpg"
        Then I receive a PageEntity object
        And PageEntity items has length of "1"
        And PageEntity item received equal to item uploaded with name "test_name"

    @testrail-C4523117
    @DAT-46538
    Scenario: List dataset items - with query - filepath
        Given There are "5" items
        And There are "5" items in remote path "/folder"
        When I list items with query filename="/folder/*"
        Then I receive a PageEntity object
        And PageEntity items has length of "5"
        And PageEntity items received have "/folder" in the filename

    @testrail-C4523117
    @DAT-46538
    Scenario: List dataset items - with query - mimetypes png
        Given There are "5" .jpg items
        And There is one .png item
        When I list items with query mimetypes="*png"
        Then I receive a PageEntity object
        And PageEntity items has length of "1"
        And And PageEntity item received equal to .png item uploadede

    @testrail-C4523117
    @DAT-46538
    Scenario: List dataset items - with query - mimetypes video
        Given There are "5" .jpg items
        And There is one .mp4 item
        When I list items with query mimetypes="video*"
        Then I receive a PageEntity object
        And PageEntity items has length of "1"
        And And PageEntity item received equal to .mp4 item uploadede


