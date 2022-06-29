@bot.create
Feature: Triggers repository get service testing

    Background: Initiate Platform Interface and create a project
        Given Platform Interface is initialized as dlp and Environment is set according to git branch
        And There is a project by the name of "triggers_get"
        And I create a dataset with a random name
        And There is a package (pushed from "triggers/item") by the name of "triggers-get"
        And There is a service by the name of "triggers-get" with module name "default_module" saved to context "service"
        And I create a cron trigger
            |name=triggers-create|function_name=run| cron=None |

    @services.delete
    @packages.delete
    @testrail-C4523174
    Scenario: Get by id
        When I get trigger by id
        Then I receive a Cron Trigger object
        And Trigger received equals to trigger created

    @services.delete
    @packages.delete
    @testrail-C4523174
    Scenario: Get by name
        When I get trigger by name
        Then I receive a Cron Trigger object
        And Trigger received equals to trigger created

