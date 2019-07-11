Feature: Project Entity repo functions

    Background: Initiate Platform Interface
        Given Platform Interface is initialized as dlp and Environment is set to development
        And There is a project by the name of "project_repo_methods"

    Scenario: Delete project
        When I delete a project Entity
        Then Project entity was deleted
        
    Scenario: Update projects name
        When I change project name to "new_project_name"
        Then Project in host has name "new_project_name"

    Scenario: Finally
        Given Clean up
