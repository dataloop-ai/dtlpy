Feature: Pipeline entity method testing actions outputs

    Background: Initiate Platform Interface and create a pipeline
        Given Platform Interface is initialized as dlp and Environment is set according to git branch
        And I create a project by the name of "test_pipeline_actions"
        And I create a dataset with a random name
        When I create a new plain recipe
        And I update dataset recipe to the new recipe


    @pipelines.delete
    @testrail-C4533387
    @DAT-48153
    Scenario: Pipeline with code node - Item should filtered by first output port
        When I create custom pipeline for code node with progress.update(action="first-output")
        And I upload item in "0000000162.jpg" to dataset
        Then I wait "5"
        And I expect that pipeline execution has "2" success executions
        And I pause pipeline in context


    @pipelines.delete
    @testrail-C4533387
    @DAT-48153
    Scenario: Pipeline with code node - Item should filtered by second output port
        When I create custom pipeline for code node with progress.update(action="second-output")
        And I upload item in "0000000162.jpg" to dataset
        Then I wait "5"
        And I expect that pipeline execution has "2" success executions
        And I pause pipeline in context


    @pipelines.delete
    @testrail-C4533387
    @DAT-48153
    Scenario: Pipeline with code node - Null input shouldn't failed the cycle pipeline
        Given I create pipeline from json in path "pipelines_json/variable_input_null.json"
        And I install pipeline in context
        And I upload item in "0000000162.jpg" to dataset
        When I execute pipeline with input type "Item"
        Then I wait "5"
        And I expect that pipeline execution has "2" success executions