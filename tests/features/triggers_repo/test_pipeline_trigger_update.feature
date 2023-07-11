Feature: Pipeline entity method testing

    Background: Initiate Platform Interface and create a pipeline
        Given Platform Interface is initialized as dlp and Environment is set according to git branch
        And I create a project by the name of "test_pipeline_flow"
        And I create a dataset with a random name
        When I create a new plain recipe
        And I update dataset recipe to the new recipe

    @pipelines.delete
    @testrail-C4532242
    @DAT-46635
    Scenario: pipeline flow
        When I create a package and service to pipeline
        And I create a pipeline from json
        And I update pipeline trigger action
        Then valid trigger updated

    @pipelines.delete
    @testrail-C4532242
    @DAT-46635
    Scenario: pipeline flow
        When I create a package and service to pipeline
        And I create a pipeline from json
        And I add trigger to the node and check installed with param keep_triggers_active equal to "False"
