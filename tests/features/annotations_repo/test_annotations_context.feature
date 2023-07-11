Feature: Annotation repository Context testing

    Background: Initiate Platform Interface and create a projects, datasets and Item
        Given Platform Interface is initialized as dlp and Environment is set according to git branch
        And I create projects by the name of "project1 project2"
        And I create datasets by the name of "dataset1 dataset2"
        And I set Dataset to Dataset 1
        And Item in path "0000000162.jpg" is uploaded to "Dataset"
        And I append item to Items
        And Classes in file: "classes_new.json" are uploaded to test Dataset
        And I have a segmentation annotation

    @testrail-C4523031
    @DAT-46421
    Scenario: Get Annotation from the Dataset it belong to
        When I get the annotation from dataset number 1
        Then Annotation dataset_id is equal to dataset 1 id
        And Annotation dataset.id is equal to dataset 1 id
        And Annotation item_id is equal to item 1 id
        And Annotation item.id is equal to item 1 id

    @testrail-C4523031
    @DAT-46421
    Scenario: Get Annotation from the Dataset it not belong to
        When I get the annotation from dataset number 2
        Then Annotation dataset_id is equal to dataset 1 id
        And Annotation dataset.id is equal to dataset 1 id
        And Annotation item_id is equal to item 1 id
        And Annotation item.id is equal to item 1 id

    @testrail-C4523031
    @DAT-46421
    Scenario: Get Annotation from the Item it belong to
        When I get the annotation from item number 1
        Then Annotation dataset_id is equal to dataset 1 id
        And Annotation dataset.id is equal to dataset 1 id
        And Annotation item_id is equal to item 1 id
        And Annotation item.id is equal to item 1 id

    @testrail-C4523031
    @DAT-46421
    Scenario: Get Annotation from the Item it not belong to
        Given I set Dataset to Dataset 2
        And Item in path "0000000162.jpg" is uploaded to "Dataset"
        And I append Item to Items
        When I get the annotation from item number 2
        Then Annotation dataset_id is equal to dataset 1 id
        And Annotation dataset.id is equal to dataset 1 id
        And Annotation item_id is equal to item 1 id
        And Annotation item.id is equal to item 1 id
