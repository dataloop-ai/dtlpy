@bot.create
Feature: Executions repository get service testing

    Background: Initiate Platform Interface and create a project
        Given Platform Interface is initialized as dlp and Environment is set according to git branch
        And I create a project by the name of "execution_get"
        And I create a dataset with a random name
        And There is a package (pushed from "executions/item") by the name of "execution-get"
        And I upload item in "0000000162.jpg" to dataset
        And There is a service by the name of "executions-get" with module name "default_module" saved to context "service"
        When I create an execution with "inputs"
            |sync=False|inputs=Item|

    @services.delete
    @packages.delete
    @testrail-C4523102
    @DAT-46519
    Scenario: Get by id
        When I get execution by id
        Then I receive an Execution object
        And Execution received equals to execution created

