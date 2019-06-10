Feature: Annotaions repository to_mask function testing

    # Background: Initiate Platform Interface
    #     Given Platform Interface is initialized as dlp and Environment is set to development
    #     And There are no projects
    #     And There is a project by the name of "Project"
    #     And I create a dataset by the name of "Dataset"
    #     And Labels in file: "labels.json" are uploaded to test Dataset
    #     And Item in path "0000000162.jpg" is uploaded to "Dataset"
    #     And There are no files in folder "downloaded_annotations"

    #need to finish
    # Scenario: Download item annotations mask
        # Given Item is annotated with annotations in file: "0162_annotations.json"
        # When I get items mask in "downloaded_annotations/maks.png"
        # Then Items mask in "downloaded_annotations/maks.png" match Items mask in "mask_should_be.png"