Feature: Deployments repository create function testing

    Background: Initiate Platform Interface and create a project
        Given Platform Interface is initialized as dlp and Environment is set to development
        And There is a project by the name of "deployments_create"
        And I create a dataset with a random name
        And There is a plugin (pushed from "deployments/item") by the name of "deployments_create"

    @deployments.delete
    @plugins.delete
    Scenario: Create Deployment
        When I create a deployment
            |deployment_name=deployments-create|plugin=deployments_create|revision=None|config=None|runtime=None|
        Then I receive a Deployment entity
