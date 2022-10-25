@bot.create
Feature: Services repository delete service testing

    Background: Initiate Platform Interface and create a project
        Given Platform Interface is initialized as dlp and Environment is set according to git branch
        And I create a project by the name of "services_delete"
        And I create a dataset with a random name
        And There is a package (pushed from "services/item") by the name of "services-delete"
        And There is a service by the name of "services-delete" with module name "default_module" saved to context "service"

    @packages.delete
    @testrail-C4523159
    Scenario: Delete by id
        When I delete service by "id"
        Then There are no services

    @packages.delete
    @testrail-C4523159
    Scenario: Delete by name
        When I delete service by "name"
        Then There are no services

    @packages.delete
    @testrail-C4523159
    Scenario: Delete by entity
        When I delete service by "entity"
        Then There are no services