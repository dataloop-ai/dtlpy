Feature: Annotation Segmentation to box

    Background: Initiate Platform Interface
        Given Platform Interface is initialized as dlp and Environment is set according to git branch
        And There is a project by the name of "Project_test_annotation_add"
        And I create a dataset with a random name
        And Item in path "0000000162.jpg" is uploaded to "Dataset"
        And Classes in file: "classes_new.json" are uploaded to test Dataset

    @testrail-C4523046
    Scenario: Segmentation to box
        Given I have a segmentation annotation
        When I execute to_box function on segmentation annotation
        Then Box will be generate

    @testrail-C4523046
    Scenario: Box from Segmentation
        Given I have a segmentation annotation
        When I create Box annotation with  from_segmentation function with mask
        Then Box will be generate

    @testrail-C4523046
    Scenario: Multi segmentation to boxes
        Given I have a multi segmentation annotations
        When I execute to_box function on segmentation annotation
        Then Boxes will be generate


    @testrail-C4523046
    Scenario: Box from Segmentation
        Given I have a multi segmentation annotations
        When I create Box annotation with  from_segmentation function with mask
        Then Boxes will be generate
