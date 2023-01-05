#Feature: Test app update
#
#    Background: Initialize
#        Given Platform Interface is initialized as dlp and Environment is set according to git branch
#        And I create a project by the name of "Project_test_app_get"
#        And I have an app entity from "apps/app.json"
#        And I install the app
#
#    @testrail-C4524925
#    Scenario: I update the app
#        When I update the app
#        Then The update should success