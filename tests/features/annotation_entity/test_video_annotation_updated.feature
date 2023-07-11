Feature: Annotation Entity update video annotation start time

    Background: Initiate Platform Interface
        Given Platform Interface is initialized as dlp and Environment is set according to git branch
        And I create a project by the name of "test_video_annotation_updated"
        And I create a dataset with a random name


    @testrail-C4532496
    @DAT-46450
    Scenario: Video - Update start time should update in snapshot
        Given Classes in file: "video_classes.json" are uploaded to test Dataset
        And Item in path "sample_video.mp4" is uploaded to "Dataset"
        When I create a blank annotation to item
        And I add frames to annotation
        And I upload annotation created
        And I update annotation start time to "1"
        Then I validate snapshot has the correct start frame


    @testrail-C4532496
    @DAT-46450
    Scenario: Audio - Update time should update annotation
        Given Classes in file: "classes_new.json" are uploaded to test Dataset
        And Item in path "simple_audio.mp3" is uploaded to "Dataset"
        When I add annotation to audio using add annotation method
        And I update annotation start time "0" end time "27"
        Then I validate audio has the correct start and end time
