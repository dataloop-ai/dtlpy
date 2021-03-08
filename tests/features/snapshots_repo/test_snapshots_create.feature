Feature: Snapshots repository create testing

    Background: Initiate Platform Interface and create a project
        Given Platform Interface is initialized as dlp and Environment is set according to git branch
        And There is a project by the name of "models_create"

    Scenario: Create a snapshot with a legal name
        Given I create a model with a random name
        And I create a snapshot with a random name
        Then Snapshot object with the same name should be exist
        And Snapshot object with the same name should be exist in host

    Scenario: Create a snapshot with an existing snapshot name
        Given I create a model with a random name
        And I create a snapshot with a random name
        When I create a snapshot with the same name
        Then "BadRequest" exception should be raised
        And "Snapshot name must be unique in model" in error message
        And No snapshot was created

#    Scenario: Create a model with an ItemBucket
#        Given I create a model with a random name
#        And I create a snapshot with a random name
#        When I push bucket from "models_codebase/dummy_codebase"
#        Then Snapshot object has ItemBucket
