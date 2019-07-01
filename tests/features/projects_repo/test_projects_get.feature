Feature: Projects repository get function testing

    Background: Initiate Platform Interface
        Given Platform Interface is initialized as dlp and Environment is set to development

    Scenario: Get an existing project by name
        Given I create a project by the name of "projects_get"
        When I get a project by the name of "projects_get"
        Then I get a project by the name of "projects_get"
        And The project I got is equal to the one created

    Scenario: Get an existing project by id
        Given I create a project by the name of "projects_get"
        When I get a project by the id of Project
        Then I get a project by the name of "projects_get"
        And The project I got is equal to the one created

    Scenario: Get non-existing project by name
        When I try to get a project by the name of "some project"
        Then "NotFound" exception should be raised

    Scenario: Get non-existing project by id
        When I try to get a project by id
        Then "NotFound" exception should be raised

    Scenario: Finally
        Given Remove cookie