Feature: Deployments repository deploy function testing

    # Background: Initiate Platform Interface and create a project
    #     Given Platform Interface is initialized as dlp and Environment is set to development
    #     And There is a project by the name of "deployments_deploy"
    #     And I create a dataset with a random name
    #     And There is a plugin (pushed from "deployments/item") by the name of "deployments_deploy"

    # @deployments.delete
    # @plugins.delete
    # Scenario: Deploy
    #     Given There are no deployments
    #     When I deploy a deployment
    #         |deployment_name=deployments-deploy|plugin=deployments_deploy|revision=None|config=None|runtime=None|
    #     Then I receive a Deployment entity
    #     When I deploy a deployment
    #         |deployment_name=deployments-deploy|plugin=deployments_deploy|revision=None|config={"new": "config"}|runtime=None|
    #     Then I receive a Deployment entity
    #     And There is only one deployment
        