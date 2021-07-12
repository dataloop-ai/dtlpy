Feature: Pipeline repository get service testing

    Background: Initiate Platform Interface
        Given Platform Interface is initialized as dlp and Environment is set according to git branch
        And There is a project by the name of "test_pipeline_delete"
        And Directory "pipeline_delete" is empty

    Scenario: Delete project by name
        When I create a pipeline with name "pipeline_delete"
        When I delete a pipeline by the name of "pipeline_delete"
        Then There are no pipeline by the name of "pipeline_delete"

    Scenario: Delete project by id
        When I create a pipeline with name "pipeline_delete_id"
        When I delete a pipeline by the id
        Then There are no pipeline by the name of "pipeline_delete_id"

    Scenario: Delete a non-existing project
        When I try to delete a pipeline by the name of "Some pipeline Name"
        Then "NotFound" exception should be raised