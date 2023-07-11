Feature: Pipeline entity method testing

    Background: Initiate Platform Interface and create a pipeline
        Given Platform Interface is initialized as dlp and Environment is set according to git branch
        And I create a project by the name of "test_pipeline_get"
        And Directory "pipeline_get" is empty

    @pipelines.delete
    @testrail-C4523143
    @DAT-46575
    Scenario: To Json
        When I create a pipeline with name "testpipeline"
        Then Object "Pipeline" to_json() equals to Platform json.

    @pipelines.delete
    @testrail-C4523143
    @DAT-46575
    Scenario: get pipeline
        When I create a pipeline with name "testpipeline"
        And I get pipeline by the name of "testpipeline"
        Then I get a pipeline entity
        And It is equal to pipeline created

