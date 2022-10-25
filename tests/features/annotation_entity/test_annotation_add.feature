Feature: Annotation Entity Add annotation

    Background: Initiate Platform Interface
        Given Platform Interface is initialized as dlp and Environment is set according to git branch
        And I create a project by the name of "Project_test_annotation_add"
        And I create a dataset with a random name

    @testrail-C4523041
    Scenario: Image - using add annotation method
        Given Classes in file: "classes_new.json" are uploaded to test Dataset
        And Item in path "0000000162.jpg" is uploaded to "Dataset"
        When I add annotation to item using add annotation method
        And I upload annotation created
        Then Item in host has annotation added

    @testrail-C4523041
    Scenario: Video - using add annotation method
        Given Classes in file: "video_classes.json" are uploaded to test Dataset
        And Item in path "sample_video.mp4" is uploaded to "Dataset"
        When I add annotation to item using add annotation method
        And I add some frames to annotation
        And I upload annotation created
        Then Item in host has annotation added

    @testrail-C4523041
    Scenario: Audio - using add annotation method
        Given Classes in file: "classes_new.json" are uploaded to test Dataset
        And Item in path "simple_audio.mp3" is uploaded to "Dataset"
        When I add annotation to audio using add annotation method
        Then audio in host has annotation added

