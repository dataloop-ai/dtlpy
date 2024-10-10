Feature: Annotations repository Upload service testing

    Background: Initiate Platform Interface
        Given Platform Interface is initialized as dlp and Environment is set according to git branch
        And I create a project by the name of "annotations_merge"
        And I create a dataset with a random name

    @DAT-78978
    Scenario: Upload annotations from file - merge
        Given Labels in file: "assets_split/annotations_upload/labels.json" are uploaded to test Dataset
        And Item in path "ann_merage/1.png" is uploaded to "Dataset"
        When I upload annotations from file: "ann_merage/1.json" with merge "True"
        And I save binary annotation coordinates
        When I upload annotations from file: "ann_merage/2.json" with merge "True"
        Then binary annotation has been merged

    @DAT-78978
    Scenario: Upload annotations from file - new 2 binary only one upload
        Given Labels in file: "assets_split/annotations_upload/labels.json" are uploaded to test Dataset
        And Item in path "ann_merage/1.png" is uploaded to "Dataset"
        When I upload annotations from file: "ann_merage/2.json" with merge "True"
        Then "8" annotations are upload



