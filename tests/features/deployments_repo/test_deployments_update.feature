Feature: Deployments repository update function testing

    # Background: Initiate Platform Interface and create a project
    #     Given Platform Interface is initialized as dlp and Environment is set to development
    #     And There is a project by the name of "deployments_update"
    #     And I create a dataset with a random name
    #     And There is a plugin (pushed from "deployments/item") by the name of "deployments_update"
    #     And There is a deployment by the name of "deployments-update"

    # @deployments.delete
    # @plugins.delete
    # Scenario: Update deployment
    #     When I update deployment
    #         |revision=2|config={"new": "config"}|runtime={"new": "runtime"}|
    #     Then I receive an updated Deployment object
    #     And Deployment attributes are modified
    #         |revision=2|config={"new": "config"}|runtime={"new": "runtime"}|