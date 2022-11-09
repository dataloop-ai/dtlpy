Feature: Annotation description with builder - image item

    Background: Initiate Platform Interface
        Given Platform Interface is initialized as dlp and Environment is set according to git branch
        And   I create a project by the name of "annotations_description_project"
        And   I create a dataset by the name of "annotations_description_dataset" in the project

    @testrail-C4532805
    Scenario: Upload classification annotation with description
        Given I upload an item of type "bmp image" to the dataset
        And   I upload "classification" annotation with description "Annotation description" to the image item
        Then  I validate annotation.description has "Annotation description" value
        When  I remove description from the annotation
        Then  I validate annotation.description has "None" value


    @testrail-C4532805
    Scenario: Upload point annotation with description
        Given I upload an item of type "jfif image" to the dataset
        And   I upload "point" annotation with description "Annotation description" to the image item
        Then  I validate annotation.description has "Annotation description" value
        When  I remove description from the annotation
        Then  I validate annotation.description has "None" value


    @testrail-C4532805
    Scenario: Upload box annotation with description
        Given I upload an item of type "jpeg image" to the dataset
        And   I upload "box" annotation with description "Annotation description" to the image item
        Then  I validate annotation.description has "Annotation description" value
        When  I remove description from the annotation
        Then  I validate annotation.description has "None" value


    @testrail-C4532805
    Scenario: Upload rotated box annotation with description
        Given I upload an item of type "jpg image" to the dataset
        And   I upload "rotated box" annotation with description "Annotation description" to the image item
        Then  I validate annotation.description has "Annotation description" value
        When  I remove description from the annotation
        Then  I validate annotation.description has "None" value


    @testrail-C4532805
    Scenario: Upload rotated cube annotation with description
        Given I upload an item of type "png image" to the dataset
        And   I upload "cube" annotation with description "Annotation description" to the image item
        Then  I validate annotation.description has "Annotation description" value
        When  I remove description from the annotation
        Then  I validate annotation.description has "None" value


    @testrail-C4532805
    Scenario: Upload semantic segmentation annotation with description
        Given I upload an item of type "tif image" to the dataset
        And   I upload "semantic segmentation" annotation with description "Annotation description" to the image item
        Then  I validate annotation.description has "Annotation description" value
        When  I remove description from the annotation
        Then  I validate annotation.description has "None" value


    @testrail-C4532805
    Scenario: Upload polygon annotation with description
        Given I upload an item of type "tiff image" to the dataset
        And   I upload "polygon" annotation with description "Annotation description" to the image item
        Then  I validate annotation.description has "Annotation description" value
        When  I remove description from the annotation
        Then  I validate annotation.description has "None" value


    @testrail-C4532805
    Scenario: Upload polyline annotation with description
        Given I upload an item of type "webp image" to the dataset
        And   I upload "polyline" annotation with description "Annotation description" to the image item
        Then  I validate annotation.description has "Annotation description" value
        When  I remove description from the annotation
        Then  I validate annotation.description has "None" value


    @testrail-C4532805
    Scenario: Upload ellipse annotation with description
        Given I upload an item of type "bmp image" to the dataset
        And   I upload "ellipse" annotation with description "Annotation description" to the image item
        Then  I validate annotation.description has "Annotation description" value
        When  I remove description from the annotation
        Then  I validate annotation.description has "None" value


    @testrail-C4532805
    Scenario: Upload note annotation with description
        Given I upload an item of type "jfif image" to the dataset
        And   I upload "note" annotation with description "Annotation description" to the image item
        Then  I validate annotation.description has "Annotation description" value
        When  I remove description from the annotation
        Then  I validate annotation.description has "None" value