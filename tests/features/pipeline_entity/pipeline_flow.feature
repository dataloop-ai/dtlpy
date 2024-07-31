Feature: Pipeline entity method testing

    Background: Initiate Platform Interface and create a pipeline
        Given Platform Interface is initialized as dlp and Environment is set according to git branch
        And I create a project by the name of "test_pipeline_flow"
        And I create a dataset with a random name
        When I create a new plain recipe
        And I update dataset recipe to the new recipe


    @pipelines.delete
    @testrail-C4523142
    @DAT-46574
    Scenario: pipeline flow
        When I create a package and service to pipeline
        And I create a pipeline from json
        And I upload item in "0000000162.jpg" to pipe dataset
        Then verify pipeline flow result

