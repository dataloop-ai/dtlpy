@qa-nightly
Feature: Items repository clone service testing

  Background: Initiate Platform Interface and create a project
    Given Platform Interface is initialized as dlp and Environment is set according to git branch
    And I create a project by the name of "items_get"
    And I create a dataset with a random name

  @DAT-83851
  Scenario: Clone item without fps metadata
    Given There is an item "without" "fps" in its metadata system
    When I clone the item
    Then The cloned item should trigger video preprocess function
    And The cloned item should have "fps" in its metadata

  @DAT-83851
  Scenario: Clone item with fps metadata
    Given There is an item "with" "fps" in its metadata system
    When I clone the item
    Then The cloned item should have "fps" in its metadata
