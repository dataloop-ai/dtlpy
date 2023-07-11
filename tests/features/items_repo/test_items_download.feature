Feature: Items repository download service testing

  Background: Initiate Platform Interface and create a project
    Given Platform Interface is initialized as dlp and Environment is set according to git branch
    And I create a project by the name of "items_download"
    And I create a dataset with a random name

    # Scenario: Download item by name - save locally
    #     Given There are no items
    #     And I upload an item by the name of "test_item.jpg"
    #     And Folder "test_items_download" is empty
    #     When I download an item by the name of "/test_item.jpg" to "test_items_download"
    #     Then There are "1" files in "test_items_download"
    #     And Item is correctly downloaded to "test_items_download/items/test_item.jpg" (compared with "0000000162.jpg")

  @testrail-C4533354
  @DAT-46533
  Scenario: Download item by id - save locally
    Given There are no items
    And I upload an item by the name of "test_item.jpg"
    And Folder "test_items_download" is empty
    When I download an item by the id to "test_items_download"
    Then There are "1" files in "test_items_download"

  @testrail-C4523112
  @DAT-46533
  Scenario: Download item by id - do not save locally
    Given There are no items
    And I upload an item by the name of "test_item.jpg"
    When I download without saving an item by the id of "/test_item.jpg"
    Then I receive item data
    When I upload item data by name of "test_item2.jpg"
    Then Item uploaded from data equals initial item uploaded

  @testrail-C4533353
  @DAT-46533
  Scenario: Download folder item
    Given There are no items
    And I upload item by the name of "test_item.jpg" to a remote path "test"
    And Folder "test_items_download" is empty
    When I download an item by the name of "/test" to "test_items_download"
    Then There are "1" files in "test_items_download"
    
  @testrail-C4533355
  @DAT-46533
  Scenario: Download item by id - do not save locally and create dir
      Given There are no items
      And I upload an item by the name of "test_item.jpg"
      When I download the item without saving and create folder
      Then file do not created

