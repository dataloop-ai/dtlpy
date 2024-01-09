Feature: publish a dpk

    Background:
        Given Platform Interface is initialized as dlp and Environment is set according to git branch
        And I create a project by the name of "test_app_ins"
        And I fetch the dpk from 'apps/app-flatten.json' file


    Scenario: publishing a dpk
        When I add context to the dpk
        And I publish a dpk to the platform
        And I add pipeline template "pipeline_flow/context.json" to the dpk
        And  I install the app
        Then The pipeline template "context-pipeline-test" should be created
