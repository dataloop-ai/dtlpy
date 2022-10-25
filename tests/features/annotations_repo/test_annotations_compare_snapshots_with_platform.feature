Feature: Annotaions repository Get service testing

    Background: Initiate Platform Interface
        Given Platform Interface is initialized as dlp and Environment is set according to git branch
        And I create a project by the name of "annotations_get"
        And I create a dataset with a random name

    @testrail-C4525771
    Scenario: Get an existing annotation by id
        Given Classes in file: "assets_split/annotations_upload/video_classes.json" are uploaded to test Dataset
        And Item in path "assets_split/annotations_upload/sample_video.mp4" is uploaded to "Dataset"
        When Item is annotated with annotations in file: "test_snapshots/snapshots_video_annotations.json"
        And I get the only annotation
        Then Annotation snapshots equal to platform snapshots
