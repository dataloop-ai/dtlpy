Feature: Bot Entity repo services

    Background: Initiate Platform Interface
        Given Platform Interface is initialized as dlp and Environment is set according to git branch
        And There is a project by the name of "bot_entity_methods"

    Scenario: Delete bot
        When I create a bot by the name of "some_bot"
        And I delete the created bot by email
        And I list bots in project
        Then I receive a bots list of "0"
