Feature: ML Subsets functionalities

    Background: Initiate Platform Interface
        Given Platform Interface is initialized as dlp and Environment is set according to git branch
        And I create a project by the name of "Project_test_ml_subsets"
        And I create a dataset with a random name
        When There are "12" items

    @DAT-83214
    Scenario: Split ML subsets with default percentages
        When I split dataset items into ML subsets with default percentages
        Then Items are splitted according to the default ratio

    @DAT-83216
    Scenario: Assign 'train' subset to selected items
        Given I select 3 specific items from the dataset
        When I assign the 'train' subset to those selected items
        Then Those items have train subset assigned

    @DAT-83217
    Scenario: Remove subsets from selected items
        Given I select 3 specific items from the dataset
        When I remove subsets from those selected items
        Then Those items have no ML subset assigned

    @DAT-83218
    Scenario: Assign subset to a single item
        Given I have a single item from the dataset
        When I assign the 'validation' subset to this item at the item level
        Then The item has 'validation' subset assigned

    @DAT-83219
    Scenario: Remove subset from a single item
        Given I have a single item with a subset assigned
        When I remove the subset from the item
        Then The item has no ML subset assigned

    @DAT-83220
    Scenario: Check item current subset
        Given I have a single item with 'test' subset assigned
        When I get the current subset of the item
        Then The result is 'test'

    @DAT-83221
    Scenario: Get items missing ML subset
        Given Some items in the dataset have subsets assigned and some do not
        When I get items missing ML subset
        Then I receive a list of item IDs with no ML subset assigned
