@bot.create
Feature: Service repository Execute items input

    Background: Initiate Platform Interface and create a project
        Given Platform Interface is initialized as dlp and Environment is set according to git branch
        And I create a project by the name of "service-items-input"
        And I create a dataset with a random name
        And There is a package (pushed from "services/items") by the name of "services-items"
        And There are "5" items

    @services.delete
    @packages.delete
    @testrail-C4533094
    Scenario: Create Service
        When I create a service
            |service_name=services-items|package=services-items|revision=None|config=None|runtime=None|
        Then I call service.execute() on items in dataset
        And Execution was executed and finished
