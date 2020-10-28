@bot.create
Feature: Triggers repository context testing

    Background: Initiate Platform Interface and create a project
        Given Platform Interface is initialized as dlp and Environment is set according to git branch
        And I create projects by the name of "trigger-context services-context2"
        And I set Project to Project 1
        And There are no datasets
        And I create a dataset with a random name
        And There is a package (pushed from "triggers/item") by the name of "triggers-context"
        And There is a service by the name of "triggers-context" with module name "default_module" saved to context "service"
        And I append service to services
        And I create a trigger
            |name=triggers-create|filters=None|resource=Item|action=Created|active=True|executionMode=Once|

    @services.delete
    @packages.delete
    Scenario: Get trigger from the project it belong to
        When I get the trigger from project number 1
        Then Trigger Project_id is equal to project 1 id
        And Trigger Project.id is equal to project 1 id
        And Trigger Service_id is equal to service 1 id
        And Trigger Service.id is equal to service 1 id

    @services.delete
    @packages.delete
    Scenario: Get trigger from the project it belong to
        When I get the trigger from project number 2
        Then Trigger Project_id is equal to project 1 id
        And Trigger Project.id is equal to project 1 id
        And Trigger Service_id is equal to service 1 id
        And Trigger Service.id is equal to service 1 id

    @services.delete
    @packages.delete
    Scenario: Get trigger from the service it belong to
        When I get the trigger from project number 1
        Then Trigger Project_id is equal to project 1 id
        And Trigger Project.id is equal to project 1 id
        And Trigger Service_id is equal to service 1 id
        And Trigger Service.id is equal to service 1 id

    @services.delete
    @packages.delete
    Scenario: Get trigger from the service it belong to
        Given There is a service by the name of "executions-context2" with module name "default_module" saved to context "service"
        And I append service to services
        When I get the trigger from project number 2
        Then Trigger Project_id is equal to project 1 id
        And Trigger Project.id is equal to project 1 id
        And Trigger Service_id is equal to service 1 id
        And Trigger Service.id is equal to service 1 id