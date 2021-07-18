Feature: Pipeline entity method testing

    Background: Initiate Platform Interface and create a pipeline
        Given Platform Interface is initialized as dlp and Environment is set according to git branch
        And There is a project by the name of "test_pipeline_list"
        And Directory "pipeline_list" is empty

    @pipelines.delete
    Scenario: test list pipeline
        When i list a project pipelines i get "0"
        And I create a pipeline with name "testpipelinelist"
        And i list a project pipelines i get "1"