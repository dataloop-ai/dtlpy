Feature: Annotation description with builder - text item

    Background: Initiate Platform Interface
        Given Platform Interface is initialized as dlp and Environment is set according to git branch
        And   I create a project by the name of "annotations_description_project"
        And   I create a dataset by the name of "annotations_description_dataset" in the project

    @testrail-C4532808
    @DAT-46441
    Scenario: Upload classification annotation with description
        Given I upload an item of type "txt text" to the dataset
        And   I upload "classification" annotation with description "Annotation description" to the text item
        Then  I validate annotation.description has "Annotation description" value
        When  I remove description from the annotation
        Then  I validate annotation.description has "None" value


    @testrail-C4532808
    @DAT-46441
    Scenario: Upload point annotation with description
        Given I upload an item of type "txt text" to the dataset
        And   I upload "text mark" annotation with description "Annotation description" to the text item
        Then  I validate annotation.description has "Annotation description" value
        When  I remove description from the annotation
        Then  I validate annotation.description has "None" value
