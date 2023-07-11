Feature: Pipeline repository get service testing

    Background: Initiate Platform Interface
        Given Platform Interface is initialized as dlp and Environment is set according to git branch
        And I create a project by the name of "test_pipeline_delete"
        And Directory "pipeline_delete" is empty

    @testrail-C4523141
    @DAT-46572
    Scenario: Delete pipeline by name
        When I create a pipeline with name "pipelinedelete"
        When I delete a pipeline by the name of "pipelinedelete"
        Then There are no pipeline by the name of "pipelinedelete"

    @testrail-C4523141
    @DAT-46572
    Scenario: Delete pipeline by id
        When I create a pipeline with name "pipelinedeleteid"
        When I delete a pipeline by the id
        Then There are no pipeline by the name of "pipelinedeleteid"

    @testrail-C4523141
    @DAT-46572
    Scenario: Delete a non-existing pipeline
        When I try to delete a pipeline by the name of "SomepipelineName"
        Then "NotFound" exception should be raised
