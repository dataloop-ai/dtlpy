Feature: Item description testing

    Background: Initiate Platform Interface
        Given Platform Interface is initialized as dlp and Environment is set according to git branch
        And There is a project by the name of "Project1"
        And I create a dataset with a random name
        And Item in path "0000000162.jpg" is uploaded to "Dataset"


    @testrail-C4532161
    Scenario: Add description to item
        When  I Add description "Item description" to item
        Then  I validate item.description has "Item description" value

    @testrail-C4532161
    Scenario: Remove field from root
        When  I Add description "Item description" to item
        Then  I validate item.description has "Item description" value
        Then  I remove description from the root
        Then  I validate item.description has "Item description" value
        And Return from and to Json functions to the original implementation

    @testrail-C4532161
    Scenario: add field to the root
        When I add new field to the root
        And  new field do not added
        Then Return from and to Json functions to the original implementation

    @testrail-C4532161
    Scenario: Delete root filed will set it to None
        When  I Add description "Item description" to item
        Then  I validate item.description has "Item description" value
        And   I remove item.description
        Then  I validate item.description is None

    @testrail-C4532161
    Scenario: Removing from no-root
        When I update item system metadata with system_metadata="True"
        Then Then I receive an Item object
        And Item in host has modified metadata
        And I update the metadata
        And Item was modified metadata
        And I remove the added metadata
        And metadata was deleted

    @testrail-C4532161
    Scenario: Set description - all options
        When I Add description "Item description1" to item with "item.description"
        Then I validate item.description has "Item description1" value
        When I Add description "Item description2" to item with "item.set_description"
        Then I validate item.description has "Item description2" value
        When I delete all the dataset items
        And  I Add description "Item description3" to item with "dataset.items.upload"
        Then I validate item.description has "Item description3" value
        When I Add description "Item description4" to item with "dataset.items.upload - overwrite=False"
        Then I validate item.description has "Item description3" value
        When I Add description "Item description5" to item with "dataset.items.upload - overwrite=True"
        Then I validate item.description has "Item description5" value

    @testrail-C4532720
    Scenario: Upload annotation with description
        Given Labels in file: "assets_split/annotations_crud/labels.json" are uploaded to test Dataset
        And Item in path "assets_split/annotations_crud/0000000162.jpg" is uploaded to "Dataset"
        When I upload an annotation with description
        Then Annotation has description