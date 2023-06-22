Feature: List the dpks

    Background:
        Given Platform Interface is initialized as dlp and Environment is set according to git branch
        And I create a project by the name of "Project_test_app_get"
        And I fetch the dpk from 'apps/app.json' file
        When I publish a dpk to the platform
        And I publish a dpk to the platform


    @testrail-C4524925
    Scenario: List the dpks
        When I list the dpks
        Then I should see at least 2 dpks

