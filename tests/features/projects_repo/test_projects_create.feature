Feature: Projects repository create service testing

    Background: Background name
        Given Platform Interface is initialized as dlp and Environment is set according to git branch

    @testrail-C4523146
    Scenario: Create project with legal name
        When I create a project by the name of "to-delete-test-project_create"
        Then Project object by the name of "to-delete-test-project_create" should be created
        And Project should exist in host by the name of "to-delete-test-project_create"


    @testrail-C4523146
    Scenario: Create project with an existing project name
        Given I create a project by the name of "to-delete-test-project_create_same_name"
        When I try to create a project by the name of "to-delete-test-project_create_same_name"
        Then "InternalServerError" exception should be raised
        And Error message includes "Failed to create project"
