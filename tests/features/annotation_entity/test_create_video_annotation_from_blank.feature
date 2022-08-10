Feature: Annotation Entity create video annotation from blank

    Background: Initiate Platform Interface
        Given Platform Interface is initialized as dlp and Environment is set according to git branch
        And There is a project by the name of "Project_test_create_video_annotation_from_blank"
        And I create a dataset with a random name

    @testrail-C4523045
    Scenario: Video - using add annotation method
        Given Classes in file: "video_classes.json" are uploaded to test Dataset
        And Item in path "sample_video.mp4" is uploaded to "Dataset"
        When I create a blank annotation to item
        And I add frames to annotation
        And I upload annotation created
        Then Item in host has video annotation added

    @testrail-C4523045
    Scenario: Video - Add annotation to video with fix frame false
        Given Classes in file: "video_classes.json" are uploaded to test Dataset
        And Item in path "sample_video.mp4" is uploaded to "Dataset"
        When I create a blank annotation to item
        And I create a false fixed annotation in video
        And I upload annotation created
        Then Video has annotation without snapshots


    @testrail-C4523045
    Scenario: Video - get annotation from dl
        Given Classes in file: "video_classes.json" are uploaded to test Dataset
        And Item in path "sample_video.mp4" is uploaded to "Dataset"
        When I create a blank annotation to item
        And I add frames to annotation
        And I upload annotation created
        And I get annotation using dl
        Then I validate annotation have frames

