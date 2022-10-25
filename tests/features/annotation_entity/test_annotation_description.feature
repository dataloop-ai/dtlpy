Feature: Annotation description

    Background: Initiate Platform Interface
        Given Platform Interface is initialized as dlp and Environment is set according to git branch
        And   I create a project by the name of "annotations_description_project"
        And   I create a dataset by the name of "annotations_description_dataset" in the project


    @testrail-C4532735
    Scenario: Add and delete annotation description to uploaded item - image item
        Given I upload an item in the path "0000000162.jpg" to the dataset
        And   I upload annotation in the path "0162_annotations.json" to the item
        When  I add description "Annotation description" to the annotation
        Then  I validate annotation.description has "Annotation description" value
        When  I remove description from the annotation
        Then  I validate annotation.description has "None" value
