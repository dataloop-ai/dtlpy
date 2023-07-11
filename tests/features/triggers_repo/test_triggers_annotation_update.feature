@bot.create
Feature: Triggers repository types - Annotation

    Background: Initiate Platform Interface and create a project
        Given Platform Interface is initialized as dlp and Environment is set according to git branch
        And I create a project by the name of "triggers_updated"
        And I create a dataset with a random name


    @services.delete
    @packages.delete
    @testrail-C4525048
    @DAT-46637
    Scenario: Updated Annotation Trigger Once
        Given There is a package (pushed from "triggers/annotation") by the name of "triggers-update"
        And There is a service by the name of "triggers-update" with module name "default_module" saved to context "service"
        When I upload item in "0000000162.jpg" to dataset
        And I annotate item
        And I create a trigger
            |name=triggers-update|filters=None|resource=Annotation|action=Updated|active=True|executionMode=Once|
        Then I receive a Trigger entity
        And I wait "5"
        And I update annotation label with new name "label_name"
        Then Service was triggered on "annotation"


    @services.delete
    @packages.delete
    @testrail-C4525048
    @DAT-46637
    Scenario: Updated Annotation Trigger Always
        Given There is a package (pushed from "triggers/annotation") by the name of "triggers-update"
        And There is a service by the name of "triggers-update" with module name "default_module" saved to context "service"
        When I upload item in "0000000162.jpg" to dataset
        When I annotate item
        When I create a trigger
            |name=triggers-update|filters=None|resource=Annotation|action=Updated|active=True|executionMode=Always|
        Then I receive a Trigger entity
        And I wait "5"
        And I update annotation label with new name "label_name"
        Then Service was triggered on "annotation"
        And I wait "5"
        And I update annotation label with new name "label_name"
        Then Service was triggered on "annotation"
