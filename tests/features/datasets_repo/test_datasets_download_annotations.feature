Feature: Datasets repository download_annotations service testing

    Background: Initiate Platform Interface and create a project
        Given Platform Interface is initialized as dlp and Environment is set according to git branch
        And I create a project by the name of "datasets_download_annotations"
        And I create a dataset with a random name
        When I add "free_text" attribute to ontology
            | key=1 | title=attr1 | scope=all |

    @testrail-C4523086
    @DAT-46494
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



