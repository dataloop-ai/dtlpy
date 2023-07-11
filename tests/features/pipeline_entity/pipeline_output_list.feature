Feature: Pipeline entity output list method testing

    Background: Initiate Platform Interface and create a pipeline
        Given Platform Interface is initialized as dlp and Environment is set according to git branch
        And I create a project by the name of "test_pipeline_outputs"
        And I create a dataset with a random name
        When I create a new plain recipe
        And I update dataset recipe to the new recipe

    @pipelines.delete
    @testrail-C4528760
    @DAT-46578
    Scenario: pipeline task node get items list
        When There are "9" items
        And I create a pipeline with code and task node
        And I upload item in "0000000162.jpg" to pipe dataset
        Then verify pipeline output result of "10" items
