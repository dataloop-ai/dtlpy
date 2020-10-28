Feature: Datasets repository Context testing

    Background: Initiate Platform Interface and create a project
        Given Platform Interface is initialized as dlp and Environment is set according to git branch
        And I create projects by the name of "project1 project2"


    Scenario: Get Dataset from the checkout Project it belong to
        Given I create datasets by the name of "dataset1 dataset2"
        When I checkout project number 1
        And I get a dataset number 1 from checkout project
        Then dataset Project.id is equal to project 1 id


    Scenario: Get Dataset from the checkout Project it is not belong to
        Given I create datasets by the name of "dataset1 dataset2"
        When I checkout project number 1
        When I get a dataset number 2 from checkout project
        Then dataset Project.id is equal to project 2 id


    Scenario: Get Dataset from the Project it is  belong to
        Given I create datasets by the name of "dataset1 dataset2"
        When I get a dataset number 1 from project number 1
        Then dataset Project.id is equal to project 1 id


    Scenario: Get Dataset from the Project it is not belong to
        Given I create datasets by the name of "dataset1 dataset2"
        When I get a dataset number 1 from project number 2
        Then dataset Project.id is equal to project 1 id
