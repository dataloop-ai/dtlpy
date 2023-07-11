Feature: publish a dpk

    Background:
        Given Platform Interface is initialized as dlp and Environment is set according to git branch
        And I create a project by the name of "test_app_ins"
        And I fetch the dpk from 'apps/app.json' file

    @testrail-C4524925
    @DAT-46514
    Scenario: publishing a dpk
        When I publish a dpk to the platform
        Then The user defined properties should have the same values
        And id, name, createdAt, codebase, url and creator should have values
