Feature: Triggers repository list function testing

    Background: Initiate Platform Interface and create a project
        Given Platform Interface is initialized as dlp and Environment is set to development
        And There is a project by the name of "triggers_list"
        And I create a dataset with a random name
        And There is a plugin (pushed from "triggers/item") by the name of "triggers_list"
        And There is a deployment by the name of "triggers-list"

    @deployments.delete
    @plugins.delete
    Scenario: List when none exist
        When I list triggers
        Then I receive a Trigger list of "0" objects

    @deployments.delete
    @plugins.delete
    Scenario: List when 1 exist
        Given I create a trigger
            |name=triggers_list|filters=None|resource=Item|action=Created|active=True|executionMode=Once|
        When I list triggers
        Then I receive a Trigger list of "1" objects

    @deployments.delete
    @plugins.delete
    Scenario: List when 2 exist
        Given I create a trigger
            |name=triggers_list_1|filters=None|resource=Item|action=Created|active=True|executionMode=Once|
        And I create a trigger
            |name=triggers_list_2|filters=None|resource=Item|action=Created|active=True|executionMode=Once|
        When I list triggers
        Then I receive a Trigger list of "2" objects