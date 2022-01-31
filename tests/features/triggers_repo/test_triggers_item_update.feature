@bot.create
Feature: Triggers repository types - item

    Background: Initiate Platform Interface and create a project
        Given Platform Interface is initialized as dlp and Environment is set according to git branch
        And There is a project by the name of "triggers_update"
        And I create a dataset with a random name


    @services.delete
    @packages.delete
    @testrail-C4525052
    Scenario: Updated Item Trigger with always
        Given There is a package (pushed from "triggers/item") by the name of "triggers-update"
        And There is a service by the name of "triggers-update" with module name "default_module" saved to context "service"
        When I upload item in "0000000162.jpg" to dataset
        Then I wait "7"
        When I create a trigger
            |name=triggers-update|filters=None|resource=Item|action=Updated|active=True|executionMode=Always|
        Then I receive a Trigger entity
        When I edit item user metadata
        Then Service was triggered on "item"
        And I wait "7"
        When I edit item user metadata
        Then Service was triggered on "item" again




