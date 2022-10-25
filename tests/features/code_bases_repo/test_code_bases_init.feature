Feature: Codebases repository Init

    Background: Initiate Platform Interface and create a project
        Given Platform Interface is initialized as dlp and Environment is set according to git branch
        And I create a project by the name of "codebases_init"
        And I create a dataset with a random name

    @testrail-C4523074
    Scenario: Init code bases with param: dataset, project, client_api
        When I init code bases with params: project, dataset, client_api
        Then I receive a code bases repository object
        And Codebases project are equal
        And Codebases dataset equal "Dataset"

    @testrail-C4523074
    Scenario: Init code bases with param: project, client_api
        When I init code bases with params: project, client_api
        Then I receive a code bases repository object
        And Codebases project are equal
        And Codebases dataset has name "Binaries"

#    @testrail-C4523074
#    Scenario: Init code bases with param: client_api
#        When I try to init code bases with params: client_api
#        Then "BadRequest" exception should be raised

    @testrail-C4523074
    Scenario: Init code bases with param: dataset, client_api
        When I init code bases with params: dataset, client_api
        Then I receive a code bases repository object
        And Codebases dataset equal "Dataset"

