Feature: Project Entity repo services

    Background: Initiate Platform Interface
        Given Platform Interface is initialized as dlp and Environment is set according to git branch
        And I create a project by the name of "project_repo_methods"

    @testrail-C4523150
    @DAT-46598
    Scenario: Delete project
        When I delete a project Entity
        Then Project entity was deleted

    @testrail-C4523150
    @DAT-46598
    Scenario: Update projects name
        When I change project name to "new_project_name"
        Then Project in host has name "new_project_name"

    @testrail-C4523150
    @DAT-46598
    Scenario: To Json
        When I reclaim project
        Then Object "Project" to_json() equals to Platform json.



