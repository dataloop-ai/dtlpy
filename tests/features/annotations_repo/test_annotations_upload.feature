Feature: Annotations repository Upload function testing

    Background: Initiate Platform Interface
        Given Platform Interface is initialized as dlp and Environment is set to development
        And There is a project by the name of "annotations_upload"
        And I create a dataset by the name of "Dataset"
    
    Scenario: Upload annotations from file
        Given Labels in file: "assets_split/annotations_upload/labels.json" are uploaded to test Dataset
        And Item in path "assets_split/annotation_collection/0000000162.jpg" is uploaded to "Dataset"
        When I upload annotations from file: "assets_split/annotations_upload/0162_annotations.json"
        Then Item should have annotations uploaded

    Scenario: Upload a single annotation
        Given Labels in file: "assets_split/annotations_upload/labels.json" are uploaded to test Dataset
        And Item in path "assets_split/annotation_collection/0000000162.jpg" is uploaded to "Dataset"
        And There is an annotation description
        When I upload annotation description to Item
        Then Item should have annotation uploaded

    # TODO - allowing me to upload illegal annotation
    # Scenario: Upload a single annotation: illegal
    #     Given There is an illegal annotation description
    #     When I try to upload annotation description to Item
    #     Then "InternalServerError" exception should be raised

    Scenario: Finally
        Given Clean up
