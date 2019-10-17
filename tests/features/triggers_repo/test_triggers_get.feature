Feature: Triggers repository get function testing

    Background: Initiate Platform Interface and create a project
        Given Platform Interface is initialized as dlp and Environment is set to development
        And There is a project by the name of "triggers_get"
        And I create a dataset with a random name
        And There is a plugin (pushed from "triggers/item") by the name of "triggers_create"
        And There is a deployment by the name of "triggers-create"
        And I create a trigger
            |name=triggers_create|filters=None|resource=Item|action=Created|active=True|executionMode=Once|

    @deployments.delete
    @plugins.delete
    Scenario: Get by id
        When I get trigger by id
        Then I receive a Trigger object
        And Trigger received equals to trigger created

    @deployments.delete
    @plugins.delete
    Scenario: Get by name
        When I get trigger by name
        Then I receive a Trigger object
        And Trigger received equals to trigger created

