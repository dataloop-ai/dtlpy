Feature: Delete dpk

    Background:
        Given Platform Interface is initialized as dlp and Environment is set according to git branch
        When I create a project by the name of "delete_dpk"
        And I fetch the dpk from 'apps/app.json' file
        And I publish a dpk to the platform

    @DAT-62990
    Scenario: Creator should be able to delete dpk should
        When I delete dpk
        And I try get the dpk by id
        Then "NotFound" exception should be raised