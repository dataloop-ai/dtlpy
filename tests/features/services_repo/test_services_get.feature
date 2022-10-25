@bot.create
Feature: Services repository get service testing

    Background: Initiate Platform Interface and create a project
        Given Platform Interface is initialized as dlp and Environment is set according to git branch
        And I create a project by the name of "services_get"
        And I create a dataset with a random name
        And There is a package (pushed from "services/item") by the name of "services-get"
        When I create a service
            |service_name=services-get|package=services-get|revision=None|config=None|runtime=None|

    @services.delete
    @packages.delete
    @testrail-C4523161
    Scenario: Get by id
        When I get service by id
        Then I receive a Service entity
        And Service received equals to service created

    @services.delete
    @packages.delete
    @testrail-C4523161
    Scenario: Get by name
        When I get service by name
        Then I receive a Service entity
        And Service received equals to service created

