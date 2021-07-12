@bot.create
Feature: Triggers repository list service testing

    Background: Initiate Platform Interface and create a project
        Given Platform Interface is initialized as dlp and Environment is set according to git branch
        And There is a project by the name of "triggers_list"
        And I create a dataset with a random name
        And There is a package (pushed from "triggers/item") by the name of "triggers-list"
        And There is a service by the name of "triggers-list" with module name "default_module" saved to context "service"

    @services.delete
    @packages.delete
    Scenario: List when none exist
        When I list triggers
        Then I receive a Trigger list of "0" objects

    @services.delete
    @packages.delete
    Scenario: List when 1 exist
        Given I create a cron trigger
            |name=triggers-list|function_name=run|
        When I list triggers
        Then I receive a Trigger list of "1" objects

    @services.delete
    @packages.delete
    Scenario: List when 2 exist
        Given I create a cron trigger
            |name=triggers-list1|function_name=run|
        Given I create a cron trigger
            |name=triggers-list2|function_name=run|
        When I list triggers
        Then I receive a Trigger list of "2" objects