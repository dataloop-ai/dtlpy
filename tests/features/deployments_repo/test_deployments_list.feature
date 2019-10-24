Feature: Deployments repository list function testing

    Background: Initiate Platform Interface and create a project
        Given Platform Interface is initialized as dlp and Environment is set to development
        And There is a project by the name of "deployments_list"
        And I create a dataset with a random name
        And There is a plugin (pushed from "deployments/item") by the name of "deployments_list"

    @deployments.delete
    @plugins.delete
    Scenario: List when none exist
        When I list deployments
        Then I receive a Deployment list of "0" objects

    @deployments.delete
    @plugins.delete
    Scenario: List when 1 exist
        When I create a deployment
            |deployment_name=deployments-list|plugin=deployments_list|revision=None|config=None|runtime=None|
        And I list deployments
        Then I receive a Deployment list of "1" objects

    @deployments.delete
    @plugins.delete
    Scenario: List when 2 exist
        When I create a deployment
            |deployment_name=deployments-list-1|plugin=deployments_list|revision=None|config=None|runtime=None|
        And I create a deployment
            |deployment_name=deployments-list-2|plugin=deployments_list|revision=None|config=None|runtime=None|
        And I list deployments
        Then I receive a Deployment list of "2" objects