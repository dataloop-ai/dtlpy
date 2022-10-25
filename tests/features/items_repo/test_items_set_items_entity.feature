Feature: Items repository set_items_entity service testing

    Background: Initiate Platform Interface and create a project
        Given Platform Interface is initialized as dlp and Environment is set according to git branch
        And I create a project by the name of "set_items_entity"
        And I create a dataset with a random name

    @testrail-C4523118
    Scenario: Change items entity to legal entity
        When I change entity to "Artifact"
        Then Items item entity is "Artifact"
        When I change entity to "Item"
        Then Items item entity is "Item"
        When I change entity to "Codebase"
        Then Items item entity is "Codebase"

    @testrail-C4523118
    Scenario: Change items entity to legal entity
        When I try to change entity to "Dataset"
        Then "Forbidden" exception should be raised

