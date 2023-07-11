@bot.create
Feature: Service repository Context testing

    Background: Initiate Platform Interface and create a project
        Given Platform Interface is initialized as dlp and Environment is set according to git branch
        And I create a project by the name of "services-flow"
        And There are no datasets
        And I create a dataset with a random name
        And There is a package (pushed from "services/item_with_init") by the name of "services-flow"
        When I upload a file in path "assets_split/items_upload/0000000162.jpg"

    @services.delete
    @packages.delete
    @testrail-C4532909
    @DAT-46604
    Scenario: Get Service from the project it belong to
        When I deploy a service with init prams
        Then I execute the service
        Then The execution success with the right output

