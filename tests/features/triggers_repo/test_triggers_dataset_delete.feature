@bot.create
Feature: Triggers repository types - dataset

    Background: Initiate Platform Interface and create a project
        Given Platform Interface is initialized as dlp and Environment is set according to git branch
        And There is a project by the name of "triggers_deleted"
        And I create a dataset with a random name


    @services.delete
    @packages.delete
    @testrail-C4525046
    Scenario: Deleted Dataset Trigger
        Given There is a package (pushed from "triggers/dataset") by the name of "triggers-delete"
        And There is a service by the name of "triggers-delete" with module name "default_module" saved to context "service"
        When I create a trigger
            |name=triggers-delete|filters=None|resource=Dataset|action=Deleted|active=True|executionMode=Once|
        Then I receive a Trigger entity
        When I delete the dataset that was created by name
        Then Service was triggered on "dataset"