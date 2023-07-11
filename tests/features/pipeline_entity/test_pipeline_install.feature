@qa-nightly
Feature: Pipeline entity method testing re-installed pipeline

    Background: Initiate Platform Interface and create a pipeline
        Given Platform Interface is initialized as dlp and Environment is set according to git branch
        And I create a project by the name of "test_code_node"
        And I create a dataset with a random name
        When I create a new plain recipe
        And I update dataset recipe to the new recipe


    @pipelines.delete
    @testrail-C4533549
    @DAT-46587
    Scenario: Remove code node from pipeline should be able to install again
        When I create a pipeline with code node
        And I pause pipeline in context
        And I delete current nodes and add dataset nodes to pipeline
        Then Pipeline status is "Installed"

