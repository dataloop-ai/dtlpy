Feature: Test app status update

    Background: Initialize
        Given Platform Interface is initialized as dlp and Environment is set according to git branch
        And I create a project by the name of "Project_test_app_status"
        And I have an app entity from "apps/app_service_fields.json"
        And I publish a dpk to the platform
        And I install the app
        And I get service by name "hello"
        And The service is active

    @DAT-68627
    Scenario: I update the app's status
        When I pause the app
        And I get service by name "hello"
        Then The deactivation should succeed
        And The service is inactive
        When I pause the app
        Then I should get an exception error='400'
        When I resume the app
        And I get service by name "hello"
        Then The activation should succeed
        And The service is active
        When I resume the app
        Then I should get an exception error='400'