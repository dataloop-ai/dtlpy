Feature: Items repository set_items_entity function testing

    Background: Initiate Platform Interface and create a project
        Given Platform Interface is initialized as dlp and Environment is set to development
        And There are no projects
        And There is a project by the name of "Project"
        And I create a dataset by the name of "Dataset"

    Scenario: Change items entity to legal entity
        When I change entity to "Artifact"
        Then Items item entity is "Artifact"
        When I change entity to "Item"
        Then Items item entity is "Item"
        When I change entity to "Package"
        Then Items item entity is "Package"

    Scenario: Change items entity to legal entity
        When I try to change entity to "Dataset"
        Then "Forbidden" exception should be raised