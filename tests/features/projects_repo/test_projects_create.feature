Feature: Projects repository create function testing

    Background: Background name
        Given Platform Interface is initialized as dlp and Environment is set to development

    Scenario: Create project with legal name
        Given There are no projects
        When I create a project by the name of "Project"
        Then Project object by the name of "Project" should be created
        And Project should exist in host

    Scenario: Create project with illegal name
        Given There are no projects
        When When I try to create a project with a blank name
        Then "InternalServerError" exception should be raised
        And There are no projects

    Scenario: Create project with an existing project name
        Given There are no projects
        And I create a project by the name of "Project"
        When I try to create a project by the name of "Project"
        Then "InternalServerError" exception should be raised
        And Error message includes "already created"
        And No project was created

