@bot.create
Feature: Executions repository context testing

    Background: Initiate Platform Interface and create a project
        Given Platform Interface is initialized as dlp and Environment is set according to git branch
        And I create projects by the name of "execution-context execution-context2"
        And I set Project to Project 1
        And There are no datasets
        And I create a dataset with a random name
        And There is a package (pushed from "executions/item") by the name of "execution-context"
        And I upload item in "0000000162.jpg" to dataset
        And There is a service by the name of "executions-get" with module name "default_module" saved to context "service"
        And I append service to services
        When I create an execution with "inputs"
            |sync=False|inputs=Item|

    @services.delete
    @packages.delete
    @testrail-C4523100
    @DAT-46517
    Scenario: Get Execution from the project it belong to
        When I get the execution from project number 1
        Then Execution Project_id is equal to project 1 id
        And Execution Project.id is equal to project 1 id
        And Execution Service_id is equal to service 1 id
        And Execution Service.id is equal to service 1 id

    @services.delete
    @packages.delete
    @testrail-C4523100
    @DAT-46517
    Scenario: Get Execution from the project it belong to
        When I get the execution from project number 2
        Then Execution Project_id is equal to project 1 id
        And Execution Project.id is equal to project 1 id
        And Execution Service_id is equal to service 1 id
        And Execution Service.id is equal to service 1 id

    @services.delete
    @packages.delete
    @testrail-C4523100
    @DAT-46517
    Scenario: Get Execution from the service it belong to
        When I get the execution from service number 1
        Then Execution Project_id is equal to project 1 id
        And Execution Project.id is equal to project 1 id
        And Execution Service_id is equal to service 1 id
        And Execution Service.id is equal to service 1 id

    @services.delete
    @packages.delete
    @testrail-C4523100
    @DAT-46517
    Scenario: Get Execution from the service it belong to
        Given There is a service by the name of "executions-context2" with module name "default_module" saved to context "service"
        And I append service to services
        When I get the execution from service number 2
        Then Execution Project_id is equal to project 1 id
        And Execution Project.id is equal to project 1 id
        And Execution Service_id is equal to service 1 id
        And Execution Service.id is equal to service 1 id
