Feature: Deployments repository delete function testing

    Background: Initiate Platform Interface and create a project
        Given Platform Interface is initialized as dlp and Environment is set to development
        And There is a project by the name of "deployments_delete"
        And I create a dataset with a random name
        And There is a plugin (pushed from "deployments/item") by the name of "deployments_delete"
        And There is a deployment by the name of "deployments-delete"

    @deployments.delete
    @plugins.delete
    Scenario: Delete by id
        When I delete deployment by "id"
        Then There are no deployments

    @deployments.delete
    @plugins.delete
    Scenario: Delete by name
        When I delete deployment by "name"
        Then There are no deployments

    @deployments.delete
    @plugins.delete
    Scenario: Delete by entity
        When I delete deployment by "entity"
        Then There are no deployments