Feature: Models repository query testing

    Background: Initiate Platform Interface and create a project
        Given Platform Interface is initialized as dlp and Environment is set according to git branch
        And There is a project by the name of "models_list"

    @testrail-C4525319
    Scenario: List by model name
        Given I create "6" models
        When I list model with filter field "name" and values "model-num-1"
        Then I get "1" entities

