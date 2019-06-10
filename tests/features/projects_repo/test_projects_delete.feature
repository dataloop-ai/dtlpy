Feature: Projects repository get function testing

    Background: Initiate Platform Interface
        Given Platform Interface is initialized as dlp and Environment is set to development

    Scenario: Delete project by name
        Given There are no projects
        And I create a project by the name of "Project"
        When I delete a project by the name of "Project"
        Then There are no projects
    
    Scenario: Delete project by id
        Given There are no projects
        And I create a project by the name of "Project"
        When I delete a project by the id of "Project"
        Then There are no projects

    Scenario: Delete a non-existing project
        Given There are no projects
        And I create a project by the name of "Project"
        When I try to delete a project by the name of "Some Project Name"
        Then "NotFound" exception should be raised
        And No project was deleted