Feature: Bots repository get service testing

    Background: Initiate Platform Interface
        Given Platform Interface is initialized as dlp and Environment is set according to git branch
        And There is a project by the name of "bots_get"


    @testrail-C4523063
    Scenario: Get an existing bot by email
        When I create a bot by the name of "some_bot"
        When I get a bot by the name of "some_bot"
        Then Received bot equals created bot