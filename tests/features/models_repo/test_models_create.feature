Feature: Models repository create testing

    Background: Initiate Platform Interface and create a project
        Given Platform Interface is initialized as dlp and Environment is set according to git branch
        And There is a project by the name of "models_create"

    @testrail-C4523124
    Scenario: Create a model with a legal name
        Given There are no models
        When I create a model with a random name
        Then Model object with the same name should be exist
        And Model object with the same name should be exist in host

    @testrail-C4523124
    Scenario: Create a model with an existing model name
        Given There are no models
        And I create a model with a random name
        When I create a model with the same name
        Then "BadRequest" exception should be raised
        And No model was created

    @testrail-C4523124
    Scenario: Create a model with an ItemCodebase
        Given There are no models
        When I create a model with a random name
        And I push codebase from "models_codebase/dummy_codebase"
        Then Model object has ItemCodebase


    @testrail-C4523124
    Scenario: Create a model with an ItemCodebase with wrong entry point
        Given There are no models
        When I create a model with a random name
        And I push codebase from "models_codebase/dummy_codebase_wrong_entry_point"
        Then "BadRequest" exception should be raised
