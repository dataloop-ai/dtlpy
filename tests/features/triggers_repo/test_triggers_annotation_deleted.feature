@bot.create
Feature: Triggers repository types - Annotation

    Background: Initiate Platform Interface and create a project
        Given Platform Interface is initialized as dlp and Environment is set according to git branch
        And I create a project by the name of "triggers_deleted"
        And I create a dataset with a random name
        And I upload item in "0000000162.jpg" to dataset


    @services.delete
    @packages.delete
    @testrail-C4525049
    @DAT-46636
    Scenario: Updated Annotation Trigger Once
        Given There is a package (pushed from "triggers/annotation") by the name of "triggers-delete"
        And There is a service by the name of "triggers-delete" with module name "default_module" saved to context "service"
        When I annotate item
        And I create a trigger
            |name=triggers-delete|filters=None|resource=Annotation|action=Deleted|active=True|executionMode=Once|
        Then I receive a Trigger entity
        And I wait "5"
        When I delete annotation from type "point" using "item" entity
        Then I validate deleted action trigger on "annotation"
