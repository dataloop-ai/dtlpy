Feature: Packages repository Init

    Background: Initiate Platform Interface and create a project
        Given Platform Interface is initialized as dlp and Environment is set to development
        And There is a project by the name of "packages_init"
        And I create a dataset with a random name

    Scenario: Init packages with param: dataset, project, client_api
        When I init packages with params: project, dataset, client_api
        Then I receive a packages repository object
        And Packages project are equal
        And Packages dataset equal "Dataset"

    Scenario: Init packages with param: project, client_api
        When I init packages with params: project, client_api
        Then I receive a packages repository object
        And Packages project are equal
        And Packages dataset has name "Binaries"

    Scenario: Init packages with param: client_api
        When I try to init packages with params: client_api
        Then "BadRequest" exception should be raised

    Scenario: Init packages with param: dataset, client_api
        When I init packages with params: dataset, client_api
        Then I receive a packages repository object
        And Packages dataset equal "Dataset"

    Scenario: Finally
        Given Clean up