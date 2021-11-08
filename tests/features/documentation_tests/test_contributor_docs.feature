Feature: Contributor Roles SDK

    Background: Initiate Platform Interface and create a project
        Given Platform Interface is initialized as dlp and Environment is set according to git branch
        And I create a project by the name of "my-project"

    Scenario: Contributor Roles SDK Scenario
        When List Members
        Then Add Members "annotator1@dataloop.ai"
        And Update Members "annotator1@dataloop.ai"
        And Remove Members "annotator1@dataloop.ai"
