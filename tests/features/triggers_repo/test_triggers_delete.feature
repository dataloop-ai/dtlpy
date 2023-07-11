@bot.create
Feature: Triggers repository delete service testing

    Background: Initiate Platform Interface and create a project
        Given Platform Interface is initialized as dlp and Environment is set according to git branch
        And I create a project by the name of "triggers_delete"
        And I create a dataset with a random name
        And There is a package (pushed from "triggers/item") by the name of "triggers-delete"
        And There is a service by the name of "triggers-delete" with module name "default_module" saved to context "service"
        And I create a trigger
            |name=triggers-create|filters=None|resource=Item|action=Created|active=True|executionMode=Once|

    @services.delete
    @packages.delete
    @testrail-C4523178
    @DAT-46644
    Scenario: Delete by id
        When I delete trigger by "id"
        Then There are no triggers

    @services.delete
    @packages.delete
    @testrail-C4523178
    @DAT-46644
    Scenario: Delete by name
        When I delete trigger by "name"
        Then There are no triggers

    @services.delete
    @packages.delete
    @testrail-C4523178
    @DAT-46644
    Scenario: Delete by entity
        When I delete trigger by "entity"
        Then There are no triggers
