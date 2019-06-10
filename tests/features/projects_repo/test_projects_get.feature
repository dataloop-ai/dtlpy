Feature: Projects repository get function testing

    Background: Initiate Platform Interface
        Given Platform Interface is initialized as dlp and Environment is set to development

    Scenario: Get an existing project by name
        Given There are no projects
        And I create a project by the name of "Project"
        When I get a project by the name of "Project"
        Then I get a project by the name of "Project"
        And The project I got is equal to the one created

    Scenario: Get an existing project by id
        Given There are no projects
        And I create a project by the name of "Project"
        When I get a project by the id of Project
        Then I get a project by the name of "Project"
        And The project I got is equal to the one created

    Scenario: Get non-existing project by name
        Given There are no projects
        When I try to get a project by the name of "Project"
        Then "NotFound" exception should be raised

    Scenario: Get non-existing project by id
        Given There are no projects
        When I try to get a project by id
        Then "NotFound" exception should be raised

