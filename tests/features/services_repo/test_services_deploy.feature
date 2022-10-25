@bot.create
Feature: Services repository deploy service testing

    Background: Initiate Platform Interface and create a project
        Given Platform Interface is initialized as dlp and Environment is set according to git branch
        And I create a project by the name of "services_deploy"
        And I create a dataset with a random name
        And There is a package (pushed from "services/item") by the name of "services-deploy"


    @services.delete
    @packages.delete
    @testrail-C4523160
    Scenario: Deploy
        Given There are no services
        When I deploy a service
            |service_name=services-deploy|package=services-deploy|revision=None|config=None|runtime=None|
        Then I receive a Service entity
        When I deploy a service
            |service_name=services-deploy|package=services-deploy|revision=None|config={"new": "config"}|runtime=None|
        Then I receive a Service entity
        And There is only one service


    @services.delete
    @packages.delete
    @testrail-C4523160
    Scenario: Deploy service from function with tabs
        When I deploy a service from function "service-with-tabs"
        Then I receive a Service entity