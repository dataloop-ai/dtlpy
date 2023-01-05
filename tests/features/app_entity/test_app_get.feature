#Feature: Test App get
#
#    Background: Initialize
#        Given Platform Interface is initialized as dlp and Environment is set according to git branch
#        When I create a project by the name of "Project_test_app_get"
#        And I have an app entity from "apps/app.json"
#        And I install the app
#
#    @testrail-C4524925
#    Scenario: Get app by name
#        When I get the app by name
#        Then I should get identical results as the json
#
#    @testrail-C4524925
#    Scenario: Get app by id
#        When I get the app by id
#        Then I should get identical results as the json
#
#    @testrail-C4524925
#    Scenario: Get app with invalid id
#        When I get the app with invalid id
#        Then I should get an exception error='400'
#
#    @testrail-C4524925
#    Scenario: Get without parameters
#        When I get the app without parameters
#        Then I should get an exception error='400'