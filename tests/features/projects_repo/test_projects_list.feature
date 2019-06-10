Feature: Projects repository list function testing

    Background: Background name
        Given Platform Interface is initialized as dlp and Environment is set to development

    Scenario: List all projects when no project exists
        Given There are no projects
        When I list all projects
        Then I receive an empty list

    Scenario: List all projects when projects exist
        Given I create a project by the name of "Project"
        When I list all projects
        Then I receive a projects list of "1" project
        And The project in the projects list equals the project I created