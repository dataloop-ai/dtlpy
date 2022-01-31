@bot.create
Feature: Triggers repository types - dataset

    Background: Initiate Platform Interface and create a project
        Given Platform Interface is initialized as dlp and Environment is set according to git branch
        And There is a project by the name of "triggers_updated"
        And I create a dataset with a random name


    @services.delete
    @packages.delete
    @testrail-C4525045
    Scenario: Updated Dataset Trigger Once
        Given There is a package (pushed from "triggers/dataset") by the name of "triggers-update"
        And There is a service by the name of "triggers-update" with module name "default_module" saved to context "service"
        When I create a trigger
            |name=triggers-update|filters=None|resource=Dataset|action=Updated|active=True|executionMode=Once|
        Then I receive a Trigger entity
        When I update dataset name to new random name
        Then Service was triggered on "dataset"


    @services.delete
    @packages.delete
    @testrail-C4525045
    Scenario: Updated Dataset Trigger Always
        Given There is a package (pushed from "triggers/dataset") by the name of "triggers-update"
        And There is a service by the name of "triggers-update" with module name "default_module" saved to context "service"
        When I create a trigger
            |name=triggers-update|filters=None|resource=Dataset|action=Updated|active=True|executionMode=Always|
        Then I receive a Trigger entity
        When I update dataset name to new random name
        Then Service was triggered on "dataset"
        When I update dataset name to new random name
        Then Service was triggered on "dataset" again



