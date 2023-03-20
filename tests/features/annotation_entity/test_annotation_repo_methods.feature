Feature: Annotation Entity repo services

    Background: Initiate Platform Interface
        Given Platform Interface is initialized as dlp and Environment is set according to git branch
        And I create a project by the name of "Project_test_annotation_repo_methods"
        And I create a dataset with a random name

    @testrail-C4523044
    Scenario: Annotation delete
        Given Labels in file: "assets_split/annotation_repo/labels.json" are uploaded to test Dataset
        And Item in path "assets_split/annotation_repo/0000000162.jpg" is uploaded to "Dataset"
        And Item is annotated with annotations in file: "assets_split/annotation_repo/0162_annotations.json"
        And There is annotation x
        When I delete entity annotation x
        Then Annotation x does not exist in item

    @testrail-C4523044
    Scenario: Updateing annotations entity
        Given Labels in file: "assets_split/annotation_repo/labels.json" are uploaded to test Dataset
        And Item in path "assets_split/annotation_repo/0000000162.jpg" is uploaded to "Dataset"
        And Item is annotated with annotations in file: "assets_split/annotation_repo/0162_annotations.json"
        And There is annotation x
        And I change annotation x label to "new_label"
        When I update annotation entity
        And I get annotation x from host
        Then Annotation x in host has label "new_label"

    @testrail-C4523044
    Scenario: Annotation download
        Given Labels in file: "assets_split/annotation_repo/labels.json" are uploaded to test Dataset
        And Item in path "assets_split/annotation_repo/0000000162.jpg" is uploaded to "Dataset"
        And Item is annotated with annotations in file: "assets_split/annotation_repo/0162_annotations.json"
        And There are no files in folder "downloaded_annotations"
        And There is annotation x
        When I download Entity annotation x with "mask" to "downloaded_annotations/mask.png"
        And I download Entity annotation x with "instance" to "downloaded_annotations/instance.png"
        Then Item annotation "mask" has been downloaded to "downloaded_annotations"
        And Item annotation "instance" has been downloaded to "downloaded_annotations"

    @testrail-C4523044
    Scenario: Uploading annotations - Image
        Given Labels in file: "assets_split/annotation_repo/labels.json" are uploaded to test Dataset
        And Item in path "assets_split/annotation_repo/0000000162.jpg" is uploaded to "Dataset"
        And I create an annotation
        When I upload annotation entity to item
        Then Item in host has annotation entity created

    @testrail-C4523044
    Scenario: Uploading annotations - Video
        Given Classes in file: "video_classes.json" are uploaded to test Dataset
        And Item in path "sample_video.mp4" is uploaded to "Dataset"
        Given I create a video annotation
        When I upload video annotation entity to item
        Then Item in host has video annotation entity created

    @DAT-44231
    Scenario: Upload items batch with random annotations
        Given Labels in file: "assets_split/annotation_repo/labels.json" are uploaded to test Dataset
        When I upload item batch from "upload_batch/to_upload"
        And I upload random x annotations
        Then analytic should say I have x annotations