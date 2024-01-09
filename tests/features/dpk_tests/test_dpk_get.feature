Feature: Get a dpk
    Background:
        Given Platform Interface is initialized as dlp and Environment is set according to git branch
        When I create a project by the name of "Project_test_dpk_get"
        And I fetch the dpk from 'apps/app.json' file
        And I publish a dpk to the platform

    @testrail-C4524925
    @DAT-46512
    Scenario: Get a valid dpk
        When I try get the dpk by id
        Then I have the same dpk as the published dpk

    @testrail-C4524925
    @DAT-46512
    Scenario: Get an invalid dpk
        When I get a dpk with invalid id
        Then I should get an exception

    @testrail-C4524925
    @DAT-46512
    Scenario: Get dpk by name
        When I get the dpk by name
        Then I have the same dpk as the published dpk