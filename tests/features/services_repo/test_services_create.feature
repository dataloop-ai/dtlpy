@bot.create
Feature: Services repository create service testing

    Background: Initiate Platform Interface and create a project
        Given Platform Interface is initialized as dlp and Environment is set according to git branch
        And I create a project by the name of "services_create"
        And I create a dataset with a random name
        And There is a package (pushed from "services/item") by the name of "services-create"

    @services.delete
    @packages.delete
    @testrail-C4523158
    @DAT-46610
    Scenario: Create Service
        When I create a service
            |service_name=services-create|package=services-create|revision=None|config=None|runtime=None|
        Then I receive a Service entity

