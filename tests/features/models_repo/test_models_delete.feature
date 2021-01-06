Feature: Models repository delete testing

    Background: Initiate Platform Interface and create a project
        Given Platform Interface is initialized as dlp and Environment is set according to git branch
        And There is a project by the name of "models_delete"

    Scenario: Delete model by name
        Given There are no models
        And I create a model with a random name
        When I delete the model that was created by name
        Then Model with same name does not exists

    Scenario: Delete model by id
        Given There are no models
        And I create a model with a random name
        When I delete the model that was created by id
        Then Model with same name does not exists

    Scenario: Delete a non-existing model
        Given There are no models
        And I create a model with a random name
        When I try to delete a model by the name of "Some Model Name"
        Then "NotFound" exception should be raised
        And No model was deleted

