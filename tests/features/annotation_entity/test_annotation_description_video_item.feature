Feature: Annotation description with builder - video item

    Background: Initiate Platform Interface
        Given Platform Interface is initialized as dlp and Environment is set according to git branch
        And   I create a project by the name of "annotations_description_project"
        And   I create a dataset by the name of "annotations_description_dataset" in the project
        When I add "free_text" attribute to ontology
            | key=1 | title=attr1 | scope=all |

    @testrail-C4532806
    @DAT-46442
    Scenario: Upload classification annotation with description
        Given I upload an item of type "webm video" to the dataset
        And   I upload "classification" annotation with description "Annotation description" to the video item
        Then  I validate annotation.description has "Annotation description" value
        When  I remove description from the annotation
        Then  I validate annotation.description has "None" value


    @testrail-C4532806
    @DAT-46442
    Scenario: Upload point annotation with description
        Given I upload an item of type "webm video" to the dataset
        And   I upload "point" annotation with description "Annotation description" to the video item
        Then  I validate annotation.description has "Annotation description" value
        When  I remove description from the annotation
        Then  I validate annotation.description has "None" value


    @testrail-C4532806
    @DAT-46442
    Scenario: Upload box annotation with description
        Given I upload an item of type "webm video" to the dataset
        And   I upload "box" annotation with description "Annotation description" to the video item
        Then  I validate annotation.description has "Annotation description" value
        When  I remove description from the annotation
        Then  I validate annotation.description has "None" value


    @testrail-C4532806
    @DAT-46442
    Scenario: Upload rotated box annotation with description
        Given I upload an item of type "webm video" to the dataset
        And   I upload "rotated box" annotation with description "Annotation description" to the video item
        Then  I validate annotation.description has "Annotation description" value
        When  I remove description from the annotation
        Then  I validate annotation.description has "None" value


    @testrail-C4532806
    @DAT-46442
    Scenario: Upload rotated cube annotation with description
        Given I upload an item of type "webm video" to the dataset
        And   I upload "cube" annotation with description "Annotation description" to the video item
        Then  I validate annotation.description has "Annotation description" value
        When  I remove description from the annotation
        Then  I validate annotation.description has "None" value


    @testrail-C4532806
    @DAT-46442
    Scenario: Upload polygon annotation with description
        Given I upload an item of type "webm video" to the dataset
        And   I upload "polygon" annotation with description "Annotation description" to the video item
        Then  I validate annotation.description has "Annotation description" value
        When  I remove description from the annotation
        Then  I validate annotation.description has "None" value


    @testrail-C4532806
    @DAT-46442
    Scenario: Upload polyline annotation with description
        Given I upload an item of type "webm video" to the dataset
        And   I upload "polyline" annotation with description "Annotation description" to the video item
        Then  I validate annotation.description has "Annotation description" value
        When  I remove description from the annotation
        Then  I validate annotation.description has "None" value


    @testrail-C4532806
    @DAT-46442
    Scenario: Upload note annotation with description
        Given I upload an item of type "webm video" to the dataset
        And   I upload "note" annotation with description "Annotation description" to the video item
        Then  I validate annotation.description has "Annotation description" value
        When  I remove description from the annotation
        Then  I validate annotation.description has "None" value
