@qa-nightly
Feature: Projects repository list service testing

    Background: Background name
        Given Platform Interface is initialized as dlp and Environment is set according to git branch

    @testrail-C4523149
    Scenario: List all projects when projects exist
        Given I create a project by the name of "projects_list"
        When I list all projects
        Then The project in the projects list equals the project I created
