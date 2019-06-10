Feature: Annotation Entity repo functions

    Background: Initiate Platform Interface
        Given Platform Interface is initialized as dlp and Environment is set to development
        And There are no projects
        And There is a project by the name of "Project"
        And I create a dataset by the name of "Dataset"
        And Labels in file: "labels.json" are uploaded to test Dataset
        And Item in path "0000000162.jpg" is uploaded to "Dataset"

    # Scenario: Annotaion to-mask 
    #     Todo

    Scenario: Annotation delete
        Given Item is annotated with annotations in file: "0162_annotations.json"
        And There is annotation x
        When I delete entity annotation x
        Then Annotation x does not exist in item

    Scenario: Annotation download
        Given Item is annotated with annotations in file: "0162_annotations.json"
        And There are no files in folder "downloaded_annotations"
        And There is annotation x
        When I download Entity annotation x with mask and instance to "downloaded_annotations/mask.png"
        Then Item annotation "mask" has been downloaded to "downloaded_annotations"
        # And Item annotation "instance" has been downloaded to "downloaded_annotations"

    Scenario: Updateing annotations entity
        Given Item is annotated with annotations in file: "0162_annotations.json"
        And There is annotation x
        And I change annotation x label to "new_label"
        When I update annotation entity
        And I get annotation x from host
        Then Annotation x in host has label "new_label"
