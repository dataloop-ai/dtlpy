@qa-nightly
Feature: Datasets repository update service testing

    Background: Initiate Platform Interface and create a project
        Given Platform Interface is initialized as dlp and Environment is set according to git branch
        And I create a project by the name of "datasets_edit"

    @testrail-C4523087
     Scenario: Change dataset name to a legal name
         Given There are no datasets
         And I create a dataset by the name of "Original_Dataset_Name"
         When I update dataset name to "New_Dataset_Name"
         Then I create a dataset by the name of "New_Dataset_Name" in host
         And There is no dataset by the name of "Original_Dataset_Name" in host
         And The dataset from host by the name of "New_Dataset_Name" is equal to the one created

      # Currently Not a bug
#     Scenario: Change dataset name to an illegal name
#         Given There are no datasets
#         And I create a dataset by the name of "Original_Dataset_Name"
#         When I try to update the "Original_Dataset_Name" name to a blank name
#         Then "BadRequest" exception should be raised

    @testrail-C4523087
     Scenario: Change dataset name to an existing dataset name
         Given There are no datasets
         And I create a dataset by the name of "Existing_Dataset_Name"
         And I create a dataset by the name of "Dataset"
         When I try to update the "Dataset" name to "Existing_Dataset_Name"
         Then "BadRequest" exception should be raised
         And I create a dataset by the name of "Existing_Dataset_Name" in host
         And I create a dataset by the name of "Dataset" in host





    