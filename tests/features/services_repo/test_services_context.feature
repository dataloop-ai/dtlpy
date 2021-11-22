@bot.create
Feature: Service repository Context testing

    Background: Initiate Platform Interface and create a project
        Given Platform Interface is initialized as dlp and Environment is set according to git branch
        And I create projects by the name of "services-get services-get2"
        And I set Project to Project 1
        And There are no datasets
        And I create a dataset with a random name
        And There is a package (pushed from "services/item") by the name of "services-get"
        And I append package to packages
        When I create a service
            |service_name=services-get|package=services-get|revision=None|config=None|runtime=None|

    @services.delete
    @packages.delete
    @testrail-C4523157
    Scenario: Get Service from the project it belong to
        When I get the service from project number 1
        Then Service Project_id is equal to project 1 id
        And Service Project.id is equal to project 1 id
        And Service Package_id is equal to package 1 id
        And Service Package.id is equal to package 1 id


    @services.delete
    @packages.delete
    @testrail-C4523157
    Scenario: Get Service from the project it not belong to
        When I get the service from project number 2
        Then Service Project_id is equal to project 1 id
        And Service Project.id is equal to project 1 id
        And Service Package_id is equal to package 1 id
        And Service Package.id is equal to package 1 id


    @services.delete
    @packages.delete
    @testrail-C4523157
    Scenario: Get Service from the package it belong to
        When I get the service from package number 1
        Then Service Project_id is equal to project 1 id
        And Service Project.id is equal to project 1 id
        And Service Package_id is equal to package 1 id
        And Service Package.id is equal to package 1 id


    @services.delete
    @packages.delete
    @testrail-C4523157
    Scenario: Get Service from the package it belong to
        Given There is a package (pushed from "services/item") by the name of "services-get"
        And I append package to packages
        When I get the service from package number 2
        Then Service Project_id is equal to project 1 id
        And Service Project.id is equal to project 1 id
        And Service Package_id is equal to package 1 id
        And Service Package.id is equal to package 1 id
