Feature: Projects repository get service testing

    Background: Initiate Platform Interface
        Given Platform Interface is initialized as dlp and Environment is set according to git branch

    @testrail-C4523147
    Scenario: Delete project by name
        Given I create a project by the name of "project_delete"
        When I delete a project by the name of "project_delete"
        Then There are no projects by the name of "project_delete"

    @testrail-C4523147
    Scenario: Delete project by id
        When I create a project by the name of "project_delete_id"
        When I delete a project by the id of "project_delete_id"
        Then There are no projects by the name of "project_delete_id"

    @testrail-C4523147
    Scenario: Delete a non-existing project
        When I try to delete a project by the name of "Some Project Name"
        Then "NotFound" exception should be raised