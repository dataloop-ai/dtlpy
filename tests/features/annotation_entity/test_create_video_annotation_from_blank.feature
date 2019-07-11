Feature: Annotation Entity create video annotation from blank

    Background: Initiate Platform Interface
        Given Platform Interface is initialized as dlp and Environment is set to development
        And There is a project by the name of "Project_test_create_video_annotation_from_blank"
        And I create a dataset by the name of "Dataset"

    Scenario: Video - using add annotation method
        Given Classes in file: "video_classes.json" are uploaded to test Dataset
        And Item in path "sample_video.mp4" is uploaded to "Dataset"
        When I create a blank annotation to item
        And I add frames to annotation
        And I upload annotation created
        Then Item in host has video annotation added

    Scenario: Finally
        Given Clean up