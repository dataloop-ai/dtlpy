Feature: Datasets repository update function testing

    Background: Initiate Platform Interface and create a project
        Given Platform Interface is initialized as dlp and Environment is set to development
        And There are no projects
        And There is a project by the name of "Project"

    #returns error - ('400', '\ntext: {"statusCode":400,"message":"\'dataset.attributes\' must be an array"}')
    # Scenario: Change dataset name to a legal name
    #     Given There are no datasets
    #     And I create a dataset by the name of "Original_Dataset_Name"
    #     When I update the "Original_Dataset_Name" name to "New_Dataset_Name"
    #     Then There is a dataset by the name of "New_Dataset_Name" in host
    #     And There is no dataset by the name of "Original_Dataset_Name" in host
    #     And The dataset from host by the name of "New_Dataset_Name" is equal to the one created

    Scenario: Change dataset name to an illegal name
        Given There are no datasets
        And I create a dataset by the name of "Original_Dataset_Name"
        When I try to update the "Original_Dataset_Name" name to a blank name
        Then "BadRequest" exception should be raised

    #need to fix bug in platform
    # Scenario: Change dataset name to an existing dataset name
    #     Given There are no datasets
    #     And I create a dataset by the name of "Existing_Dataset_Name"
    #     And I create a dataset by the name of "Dataset"
    #     When I try to update the "Dataset" name to "Existing_Dataset_Name"
    #     Then "BadRequest" exception should be raised
    #     And There is a dataset by the name of "Existing_Dataset_Name" in host
    #     And There is a dataset by the name of "Dataset" in host



    