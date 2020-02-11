@bot.create
Feature: Executions repository list service testing

    @services.delete
    @packages.delete
    Scenario: Initiate Platform Interface and create a project
        Given Platform Interface is initialized as dlp and Environment is set according to git branch
        And There is a project by the name of "execution_list"
        And I create a dataset with a random name
        And There is a package (pushed from "executions/item") by the name of "execution_list"
        And I upload item in "0000000162.jpg" to dataset
        And There is a service by the name of "executions-list" with module name "default_module" saved to context "service"
        When I list service executions
        Then I receive a list of "0" executions
        When I create an execution with "inputs"
            |sync=False|inputs=Item|
        And I list service executions
        Then I receive a list of "1" executions
        When I create an execution with "inputs"
            |sync=False|inputs=Item|
        And I list service executions
        Then I receive a list of "2" executions