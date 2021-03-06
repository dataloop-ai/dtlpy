Feature: Bots repository get service testing

    Background: Initiate Platform Interface
        Given Platform Interface is initialized as dlp and Environment is set according to git branch
        Given There is a project by the name of "bot_delete"

    Scenario: Delete bot by id
        When I create a bot by the name of "some_bot"
        And I delete the created bot by email
        And I list bots in project
        Then I receive a bots list of "0"

    Scenario: Delete a non-existing bot
        When I try to delete a bot by the name of "Some Bot Name"
        Then "NotFound" exception should be raised