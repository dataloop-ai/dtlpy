Feature: Project Entity repo services

    Background: Initiate Platform Interface
        Given Platform Interface is initialized as dlp and Environment is set according to git branch
        And There is a project by the name of "project_repo_methods"

    Scenario: Delete project
        When I delete a project Entity
        Then Project entity was deleted
        
    Scenario: Update projects name
        When I change project name to "new_project_name"
        Then Project in host has name "new_project_name"

    Scenario: To Json
        When I reclaim project
        Then Object "Project" to_json() equals to Platform json.


