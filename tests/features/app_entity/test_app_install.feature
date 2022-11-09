Feature: App entity install App

    Background: Initialize
        Given Platform Interface is initialized as dlp and Environment is set according to git branch
        And I create a project by the name of "test_app_ins"
        And I have an app entity from "apps/app.json"
        And publish the app

    @testrail-C4524925
    Scenario: Install a valid app
        When I install the app
        Then I should get the app with the same id

    @testrail-C4524925
    Scenario: Installing identical app
        When I install the app
        And I install the app with exception
        Then I should get an exception error='3232'

    

