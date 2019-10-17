Feature: Triggers repository create function testing

    Background: Initiate Platform Interface and create a project
        Given Platform Interface is initialized as dlp and Environment is set to development
        And There is a project by the name of "triggers_create"
        And I create a dataset with a random name

    @deployments.delete
    @plugins.delete
    Scenario: Created Item Trigger
        Given There is a plugin (pushed from "triggers/item") by the name of "triggers_create"
        And There is a deployment by the name of "triggers-create"
        When I create a trigger
            |name=triggers_create|filters=None|resource=Item|action=Created|active=True|executionMode=Once|
        Then I receive a Trigger entity
        When I upload item in "0000000162.jpg" to dataset
        Then Deployment was triggered on "item"

    @deployments.delete
    @plugins.delete
    Scenario: Updated Item Trigger
        Given There is a plugin (pushed from "triggers/item") by the name of "triggers_create"
        And There is a deployment by the name of "triggers-create"
        When I upload item in "0000000162.jpg" to dataset
        Then I wait "7"
        When I create a trigger
            |name=triggers_create|filters=None|resource=Item|action=Updated|active=True|executionMode=Once|
        Then I receive a Trigger entity
        When I edit item user metadata
        Then Deployment was triggered on "item"

    # # TODO - bug in piper - session has no inputs - annotation triggers are not yet supported
    # @deployments.delete
    # @plugins.delete
    # Scenario: Created Annotation Trigger
    #     Given There is a plugin (pushed from "triggers/annotation") by the name of "triggers_create"
    #     And There is a deployment by the name of "triggers-create"
    #     When I upload item in "0000000162.jpg" to dataset
    #     And I create a trigger
    #         |name=triggers_create|filters=None|resource=Annotation|action=Created|active=True|executionMode=Once|
    #     Then I receive a Trigger entity
    #     When I annotate item
    #     Then Deployment was triggered on "annotation"