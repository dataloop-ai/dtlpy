Feature: Datasets repository download_annotations function testing

    Background: Initiate Platform Interface and create a project
        Given Platform Interface is initialized as dlp and Environment is set to development
        And There is a project by the name of "datasets_download_annotations"
        And I create a dataset with a random name

    Scenario: Download existing annotations
        Given Item in path "0000000162.png" is uploaded to "Dataset"
        And There are a few annotations in the item
        And There is no folder by the name of "json" in assets folder
        When I download dataset annotations
        Then I get a folder named "json" in assets folder
        And Annotations downloaded equal to the annotations uploaded

    # Scenario: Download annotations when no annotation exist
    #     Given Item in path "0000000162.png" is uploaded to "Dataset"
    #     And There is no folder by the name of "json" in assets folder
    #     When I download dataset annotations
    #     Then I get a folder named "json" in assets folder
    #     And The folder named "json" in folder assets is empty

    Scenario: Finally
        Given Clean up
