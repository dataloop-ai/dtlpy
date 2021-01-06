Feature: Models repository create testing

    Background: Initiate Platform Interface and create a project
        Given Platform Interface is initialized as dlp and Environment is set according to git branch
        And There is a project by the name of "model.update"

    Scenario: Create a model with a legal name
        Given There are no models
        When I create a model with a random name
        Then Model object with the same name should be exist
        And Model object with the same name should be exist in host

    Scenario: Create a model with an existing model name
        Given There are no models
        And I create a model with a random name
        When I try to create a model by the same name
        Then "BadRequest" exception should be raised
        And No model was created

