Feature: Annotations repository Upload service testing

    Background: Initiate Platform Interface
        Given Platform Interface is initialized as dlp and Environment is set according to git branch
        And I create a project by the name of "annotations_upload"
        And I create a dataset with a random name
        When I add "free_text" attribute to ontology
            | key=1 | title=attr1 | scope=all |

    @testrail-C4523039
    @DAT-46433
    Scenario: Upload annotations from file
        Given Labels in file: "assets_split/annotations_upload/labels.json" are uploaded to test Dataset
        And Item in path "assets_split/annotation_collection/0000000162.jpg" is uploaded to "Dataset"
        When I upload annotations from file: "assets_split/annotations_upload/0162_annotations.json" with merge "False"
        Then Item should have annotations uploaded

    @testrail-C4523039
    @DAT-46433
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



