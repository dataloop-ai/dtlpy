@bot.create
Feature: Triggers repository types - item

    Background: Initiate Platform Interface and create a project
        Given Platform Interface is initialized as dlp and Environment is set according to git branch
        And There is a project by the name of "triggers_deleted"
        And I create a dataset with a random name
        And I upload item in "0000000162.jpg" to dataset


    @services.delete
    @packages.delete
    @testrail-C4525043
    Scenario: Deleted Item Trigger with once
        Given There is a package (pushed from "triggers/item") by the name of "triggers-delete"
        And There is a service by the name of "triggers-delete" with module name "default_module" saved to context "service"
        When I create a trigger
            |name=triggers-deleted|filters=None|resource=Item|action=Deleted|active=True|executionMode=Once|
        Then I receive a Trigger entity
        And I wait "5"
        When I delete the item by id
        Then I wait "5"
        And I validate deleted action trigger on "item"