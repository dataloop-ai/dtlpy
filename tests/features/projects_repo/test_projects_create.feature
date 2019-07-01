Feature: Projects repository create function testing

    Background: Background name
        Given Platform Interface is initialized as dlp and Environment is set to development

    Scenario: Create project with legal name
        When I create a project by the name of "project_create"
        Then Project object by the name of "project_create" should be created
        And Project should exist in host by the name of "project_create"

#    Scenario: Create project with illegal name
#        When When I try to create a project with a blank name
#        Then "InternalServerError" exception should be raised

    Scenario: Create project with an existing project name
        Given I create a project by the name of "project_create_same_name"
        When I try to create a project by the name of "project_create_same_name"
        Then "InternalServerError" exception should be raised
        And Error message includes "already created"

    Scenario: Finally
        Given Remove cookie
