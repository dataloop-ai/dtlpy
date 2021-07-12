@bot.create
Feature: Triggers repository delete service testing

    Background: Initiate Platform Interface and create a project
        Given Platform Interface is initialized as dlp and Environment is set according to git branch
        And There is a project by the name of "triggers_delete"
        And I create a dataset with a random name
        And There is a package (pushed from "triggers/item") by the name of "triggers-delete"
        And There is a service by the name of "triggers-delete" with module name "default_module" saved to context "service"
        And I create a cron trigger
            |name=triggers-create|function_name=run|

    @services.delete
    @packages.delete
    Scenario: Delete by id
        When I delete trigger by "id"
        Then There are no triggers

    @services.delete
    @packages.delete
    Scenario: Delete by name
        When I delete trigger by "name"
        Then There are no triggers

    @services.delete
    @packages.delete
    Scenario: Delete by entity
        When I delete trigger by "entity"
        Then There are no triggers