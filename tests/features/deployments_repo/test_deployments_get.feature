Feature: Deployments repository get function testing

    Background: Initiate Platform Interface and create a project
        Given Platform Interface is initialized as dlp and Environment is set to development
        And There is a project by the name of "deployments_get"
        And I create a dataset with a random name
        And There is a plugin (pushed from "deployments/item") by the name of "deployments_get"
        When I create a deployment
            |deployment_name=deployments-get|plugin=deployments_get|revision=None|config=None|runtime=None|

    @deployments.delete
    @plugins.delete
    Scenario: Get by id
        When I get deployment by id
        Then I receive a Deployment entity
        And Deployment received equals to deployment created

    @deployments.delete
    @plugins.delete
    Scenario: Get by name
        When I get deployment by name
        Then I receive a Deployment entity
        And Deployment received equals to deployment created

