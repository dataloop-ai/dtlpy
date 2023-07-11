Feature: Items repository Context testing

    Background: Initiate Platform Interface and create a projects, datasets and Item
        Given Platform Interface is initialized as dlp and Environment is set according to git branch
        And I create projects by the name of "project1 project2"
        And I create datasets by the name of "dataset1 dataset2"
        And I set Dataset to Dataset 1
        And Item in path "0000000162.jpg" is uploaded to "Dataset"
#        And I append Item to Items
#        And I set Dataset to Dataset 2
#        And Item in path "0000000162.jpg" is uploaded to "Dataset"
#        And I set item to Item 2

    @testrail-C4523110
    @DAT-46531
    Scenario: Get Item from the Project it belong to
        When I get the item from project number 1
        Then item dataset_id is equal to dataset 1 id
        And item dataset.id is equal to dataset 1 id
#        after DAT-5663  will be ended
#        And item ProjectId is equal to project 1 id
        And item Project.id is equal to project 1 id

#   after DAT-5663  will be ended
#   Scenario: Get Item from the Project it not belong to
#        When I get the item from project number 2
#        Then item dataset_id is equal to dataset 1 id
#        And item dataset.id is equal to dataset 1 id
#        And item ProjectId is equal to project 1 id
#        And item Project.id is equal to project 1 id

    @testrail-C4523110
    @DAT-46531
    Scenario: Get Item from the Dataset it belong to
        When I get the item from dataset number 1
        Then item dataset_id is equal to dataset 1 id
        And item dataset.id is equal to dataset 1 id
#        after DAT-5663  will be ended
#        And item ProjectId is equal to project 1 id
        And item Project.id is equal to project 1 id

    @testrail-C4523110
    @DAT-46531
    Scenario: Get Item from the Dataset it not belong to
        When I get the item from dataset number 2
        Then item dataset_id is equal to dataset 1 id
        And item dataset.id is equal to dataset 1 id
#        after DAT-5663  will be ended
#        And item ProjectId is equal to project 1 id
#        And item Project.id is equal to project 1 id
