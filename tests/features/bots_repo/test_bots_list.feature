Feature: Bots repository list service testing

    Background: Background name
        Given Platform Interface is initialized as dlp and Environment is set according to git branch
        And There is a project by the name of "bots_list"

    Scenario: List one bot
        Given There are no bots in project
        When I create a bot by the name of "first_bot"
        And I list bots in project
        Then I receive a bots list of "1"

    Scenario: List two bot
        Given There are no bots in project
        When I create a bot by the name of "first_bot"
        And I create a bot by the name of "second_bot"
        And I list bots in project
        Then I receive a bots list of "2"
