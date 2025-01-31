Feature: Annotation Entity create video annotation from blank

    Background: Initiate Platform Interface
        Given Platform Interface is initialized as dlp and Environment is set according to git branch
        And I create a project by the name of "Project_test_create_video_annotation_from_blank"
        And I create a dataset with a random name
        When I add "free_text" attribute to ontology
            | key=1 | title=attr1 | scope=all |
        When I add "free_text" attribute to ontology
            | key=2 | title=attr2 | scope=all |

    @testrail-C4523045
    @DAT-46446
    Scenario: Video - using add annotation method
        Given Classes in file: "video_classes.json" are uploaded to test Dataset
        And Item in path "sample_video.mp4" is uploaded to "Dataset"
        When I create a blank annotation to item
        And I add frames to annotation
        And I upload annotation created
        Then Item in host has video annotation added

    @testrail-C4523045
    @DAT-46446
    Scenario: Video - Add annotation to video with fix frame false
        Given Classes in file: "video_classes.json" are uploaded to test Dataset
        And Item in path "sample_video.mp4" is uploaded to "Dataset"
        When I create a blank annotation to item
        And I create a false fixed annotation in video
        And I upload annotation created
        Then Video has annotation without snapshots


    @testrail-C4523045
    @DAT-46446
    Scenario: Video - get annotation from dl
        Given Classes in file: "video_classes.json" are uploaded to test Dataset
        And Item in path "sample_video.mp4" is uploaded to "Dataset"
        When I create a blank annotation to item
        And I add frames to annotation
        And I upload annotation created
        And I get annotation using dl
        Then I validate annotation have frames

    @testrail-C4523045
    @DAT-46446
    Scenario: Video - change attrs for frames
        Given Classes in file: "video_classes.json" are uploaded to test Dataset
        And Item in path "sample_video.mp4" is uploaded to "Dataset"
        When I add class annotation to item using add annotation method
        And I set frame "3" annotation attributes
        And I upload annotation created
        Then I validity "3" has the updated attributes
