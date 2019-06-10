Feature: Annotaions repository download function testing

    Background: Initiate Platform Interface
        Given Platform Interface is initialized as dlp and Environment is set to development
        And There are no projects
        And There is a project by the name of "Project"
        And I create a dataset by the name of "Dataset"
        And Labels in file: "labels.json" are uploaded to test Dataset
        And Item in path "0000000162.jpg" is uploaded to "Dataset"
        And There are no files in folder "downloaded_annotations"
        
    Scenario: Download item annotations with mask
        Given Item is annotated with annotations in file: "0162_annotations.json"
        When I download items annotations with mask to "downloaded_annotations/mask.png"
        Then Item annotation "mask" has been downloaded to "downloaded_annotations"
        # And "Mask" is correctlly downloaded (compared with "mask_should_be.png")

    Scenario: Download item annotations with instance
        Given Item is annotated with annotations in file: "0162_annotations.json"
        When I download items annotations with instance to "downloaded_annotations/instance.png"
        Then Item annotation "instance" has been downloaded to "downloaded_annotations"
        # And "Instance" is correctlly downloaded (compared with "instance_should_be.png")

