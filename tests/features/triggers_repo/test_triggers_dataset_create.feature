@bot.create
Feature: Triggers repository types - dataset

    Background: Initiate Platform Interface and create a project
        Given Platform Interface is initialized as dlp and Environment is set according to git branch
        And I create a project by the name of "triggers_created"
        And I create a dataset with a random name


    @services.delete
    @packages.delete
    @testrail-C4525044
    @DAT-46641
    Scenario: Created Dataset Trigger
        Given There is a package (pushed from "triggers/dataset") by the name of "triggers-create"
        And There is a service by the name of "triggers-create" with module name "default_module" saved to context "service"
        When I create a trigger
            |name=triggers-create|filters=None|resource=Dataset|action=Created|active=True|executionMode=Once|
        Then I receive a Trigger entity
        Given I create a dataset with a random name
        Then Service was triggered on "dataset"
