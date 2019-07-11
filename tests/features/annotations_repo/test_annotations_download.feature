Feature: Annotaions repository download function testing

    Background: Initiate Platform Interface
        Given Platform Interface is initialized as dlp and Environment is set to development
        And There is a project by the name of "Project_annotations_download"
        And I create a dataset by the name of "Dataset"
        
    Scenario: Download item annotations with mask
        Given Labels in file: "assets_split/annotations_download/labels.json" are uploaded to test Dataset
        And Item in path "assets_split/annotations_download/0000000162.jpg" is uploaded to "Dataset"
        And There are no files in folder "downloaded_annotations"
        And Item is annotated with annotations in file: "assets_split/annotations_download/0162_annotations.json"
        When I download items annotations with mask to "downloaded_annotations/mask.png"
        Then Item annotation "mask" has been downloaded to "downloaded_annotations"

    Scenario: Download item annotations with instance
        Given Labels in file: "assets_split/annotations_download/labels.json" are uploaded to test Dataset
        And Item in path "assets_split/annotations_download/0000000162.jpg" is uploaded to "Dataset"
        And There are no files in folder "downloaded_annotations"
        And Item is annotated with annotations in file: "assets_split/annotations_download/0162_annotations.json"
        When I download items annotations with instance to "downloaded_annotations/instance.png"
        Then Item annotation "instance" has been downloaded to "downloaded_annotations"

    Scenario: Finally
        Given Clean up

