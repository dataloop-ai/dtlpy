Feature: Bots repository create service testing

    Background: Background name
        Given Platform Interface is initialized as dlp and Environment is set according to git branch
        And I create a project by the name of "bot_entity_methods"

    @testrail-C4523061
    Scenario: Create bot with legal name
        When I create a bot by the name of "some_bot"
        And I list bots in project
        Then a bot with name "some_bot" exists in bots list
