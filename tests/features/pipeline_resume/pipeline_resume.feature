Feature: Resuming Pipeline

    Background: Initiate Platform Interface and create a pipeline
        Given Platform Interface is initialized as dlp and Environment is set according to git branch
        And I create a project by the name of "test_pipeline_flow"
        And I create a dataset with a random name

    @services.delete
    @pipelines.delete
    Scenario: Resuming pipeline
        Given I create a package and service to pipeline
        And I have a resumable pipeline
        And I install pipeline in context
        And Faas node service is paused
        And Item in path "assets_split/annotations_crud/0000000162.jpg" is uploaded to "Dataset"
        And Item reached task node
        When I pause pipeline in context
        And I complete item in task
        And I wait "5"
        Then Next nodes should not be executed
        When I resume pipeline with resume option "resumeExistingCycles"
        Then Next nodes should be executed
        When I pause pipeline in context
        And I wait "5"
        Given Faas node execution is in queue
        When Faas node service is resumed
        And Faas node service has completed
        And I resume pipeline with resume option "resumeExistingCycles"
        Then Item proceeded to next node