Feature: Pipeline node input handling

    Background: Initiate Platform Interface and create a pipeline
        Given Platform Interface is initialized as dlp and Environment is set according to git branch
        And I create a project by the name of "test_pipeline_flow"


    @DAT-54491
    @pipelines.delete
    Scenario: First node passes input and the second node function has default input in case of missing input
        When I build a pipeline where the second node handles missing input
        And I execute pipeline with input type: "String" and input value: "string_from_root"
        Then Pipeline has "1" cycle executions
        And Cycle completed with save "True"
        And Cycle "1" status is "success"
        And Cycle "1" node "2" execution "1" single output is: "string_from_root"

    @DAT-54490
    @pipelines.delete
    Scenario: First node passes input and the second node function has no default input in case of missing input
        When I build a pipeline where the second node does not handle missing input
        And I execute pipeline with input type: "String" and input value: "string_from_root"
        Then Pipeline has "1" cycle executions
        And Cycle completed with save "True"
        And Cycle "1" status is "success"
        And Cycle "1" node "2" execution "1" single output is: "string_from_root"


