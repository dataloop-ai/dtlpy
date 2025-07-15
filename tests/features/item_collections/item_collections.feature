Feature: Item Collections

  Background: Initialize Platform Interface
    Given Platform Interface is initialized as dlp and Environment is set according to git branch
    And I create a project by the name of "Project_test_collections"
    And I create a dataset with a random name

  @DAT-85364
  Scenario: Create a new collection
    When I create a collection with the name "Justice League"
    Then The collection "Justice League" is created successfully

  @DAT-85365
  Scenario: Create a collection with a duplicate name
    Given I have an existing collection named "Justice League"
    When I try to create a collection with the name "Justice League"
    Then I receive an error stating that the collection name already exists

  @DAT-85366
  Scenario: Update an existing collection's name
    Given I have an existing collection named "Justice League"
    When I update the collection name to "Avengers"
    Then The collection name is updated to "Avengers"

  @DAT-85367
  Scenario: Delete an existing collection
    Given I have an existing collection named "Justice League"
    When I delete the collection "Justice League"
    Then The collection "Justice League" is deleted successfully

  @DAT-85368
  Scenario: Clone an existing collection
    Given I have an existing collection named "Justice League"
    When I clone the collection "Justice League"
    Then A new collection with the name "Justice League-clone-1" is created

  @DAT-85369
  Scenario: List all collections in the dataset
    Given I have multiple collections in the dataset
    When I list all collections
    Then I receive a list of all collections with their names and keys

  @DAT-85370
  Scenario: Assign an item to a collection
    Given I have an item in the dataset
    When I assign the item to the collection "Justice League"
    Then The item is assigned to the collection "Justice League"

  @DAT-85735
  Scenario: Cloning a collection - the new collection should have the same items as the cloned collection
    When I create a collection with the name "Cloning Collection"
    Given I have an item in the dataset
    When I assign the item to the collection "Cloning Collection"
    When I clone the collection "Cloning Collection"
    Then The item is assigned to the collection "Cloning Collection-clone-1"

  @DAT-98058
  Scenario: Assign an item to a collection
    Given I upload an item by the name of "test_item.jpg"
    Given I have an item in the dataset
    When  I assign the item to the collection "Justice League"
    Then The item is assigned to the collection "Justice League"
    When I list all unassigned items
    Then I expect to see "1" unassigned items