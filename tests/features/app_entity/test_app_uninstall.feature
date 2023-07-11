Feature: Test App uninstall

    Background: Initialize
        Given Platform Interface is initialized as dlp and Environment is set according to git branch
        And I create a project by the name of "Project_test_app_get"
        And I have an app entity from "apps/app.json"
        And I publish a dpk to the platform
        And I install the app

    @testrail-C4524925
    @DAT-46454
    Scenario: Uninstall the app
        Given I uninstall the app
        Then The app shouldn't be in listed

    @testrail-C4524925
    @DAT-46454
    Scenario: I uninstall an invalid app
        Given I uninstall not existed app
        Then I should get an exception error='500'