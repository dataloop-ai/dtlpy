@bot.create
Feature: Services repository list service testing

    Background: Initiate Platform Interface and create a project
        Given Platform Interface is initialized as dlp and Environment is set according to git branch
        And There is a project by the name of "services_list"
        And I create a dataset with a random name
        And There is a package (pushed from "services/item") by the name of "services-list"

    @services.delete
    @packages.delete
    @testrail-C4523162
    Scenario: List when none exist
        When I list services
        Then I receive a Service list of "0" objects

    @services.delete
    @packages.delete
    @testrail-C4523162
    Scenario: List when 1 exist
        When I create a service
            |service_name=services-list|package=services-list|revision=None|config=None|runtime=None|
        And I list services
        Then I receive a Service list of "1" objects

    @services.delete
    @packages.delete
    @testrail-C4523162
    Scenario: List when 2 exist
        When I create a service
            |service_name=services-list-1|package=services-list|revision=None|config=None|runtime=None|
        And I create a service
            |service_name=services-list-2|package=services-list|revision=None|config=None|runtime=None|
        And I list services
        Then I receive a Service list of "2" objects