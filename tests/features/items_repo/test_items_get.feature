@qa-nightly
Feature: Items repository get service testing

  Background: Initiate Platform Interface and create a project
    Given Platform Interface is initialized as dlp and Environment is set according to git branch
    And I create a project by the name of "items_get"
    And I create a dataset with a random name

  @testrail-C4523116
  @DAT-46537
  Scenario: Get an existing item by id
    Given There is an item
    When I get the item by id
    Then I receive an Item object
    And The item I received equals the item I uploaded

  @testrail-C4523116
  @DAT-46537
  Scenario: Get an non-existing item by id
    When I try to get item by "some_id"
    Then "NotFound" exception should be raised

  @testrail-C4523116
  @DAT-46537
  Scenario: Get an existing item by remote path
    Given There is an item
    When I get the item by remote path "/0000000162.jpg"
    Then I receive an Item object
    And The item I received equals the item I uploaded

  @testrail-C4523116
  @DAT-46537
  Scenario: Get a non-existing item by remote path
    When I try to get an item by remote path "/some_path"
    Then "NotFound" exception should be raised

  @testrail-C4523116
  @DAT-46537
  Scenario: Use get service with neither filename or remote path
    When I try to use get services with no params
    Then "BadRequest" exception should be raised

  @testrail-C4523116
  @DAT-46537
  Scenario: Get an existing item by filename when 2 files with the same name exist
    Given There are 2 items by the name of "0000000162.jpg"
    When I try to get an item by remote path "**/0000000162.jpg"
    Then "NotFound" exception should be raised

  @testrail-C4523116
  @DAT-46537
  Scenario: Get dataset items by dataset Id
    Given There are 2 items by the name of "0000000162.jpg"
    Then I get items by dataset Id


  @DAT-86214
  Scenario: Get an existing item by remote path with no type
    When I upload item in "notype"
    When I get the item by remote path "/notype"
    Then I receive an Item object
    And The item I received equals the item I uploaded

  @skip_test
  @DAT-84281
  @DM-cache
  Scenario: Get an existing item by id from cache
    Given There is an item
    When I get the item by id
    And I wait "1"
    When I get the item by id
    Then I receive an Item object
    And The item I received equals the item I uploaded