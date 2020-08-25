Feature: Projects repository create service testing

    Background: Background name
        Given Platform Interface is initialized as dlp and Environment is set according to git branch

    Scenario: Create project with legal name
        When I create a project by the name of "to-delete-test-project_create"
        Then Project object by the name of "to-delete-test-project_create" should be created
        And Project should exist in host by the name of "to-delete-test-project_create"


    Scenario: Create project with an existing project name
        Given I create a project by the name of "to-delete-test-project_create_same_name"
        When I try to create a project by the name of "to-delete-test-project_create_same_name"
        # TODO - this line is different in prod and in rc - need to open a jira ticket for Assaf
        Then I receive error with status code "500"
