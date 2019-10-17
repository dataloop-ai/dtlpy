Feature: Triggers repository delete function testing

    Background: Initiate Platform Interface and create a project
        Given Platform Interface is initialized as dlp and Environment is set to development
        And There is a project by the name of "triggers_delete"
        And I create a dataset with a random name
        And There is a plugin (pushed from "triggers/item") by the name of "triggers_delete"
        And There is a deployment by the name of "triggers-delete"
        And I create a trigger
            |name=triggers_create|filters=None|resource=Item|action=Created|active=True|executionMode=Once|

    @deployments.delete
    @plugins.delete
    Scenario: Delete by id
        When I delete trigger by "id"
        Then There are no triggers

    @deployments.delete
    @plugins.delete
    Scenario: Delete by name
        When I delete trigger by "name"
        Then There are no triggers

    @deployments.delete
    @plugins.delete
    Scenario: Delete by entity
        When I delete trigger by "entity"
        Then There are no triggers