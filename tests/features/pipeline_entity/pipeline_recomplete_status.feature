Feature: Pipeline entity method testing recomplete items

    Background: Initiate Platform Interface and create a pipeline
        Given Platform Interface is initialized as dlp and Environment is set according to git branch
        And There is a project by the name of "test_pipeline_recomplete"
        And I create a dataset with a random name
        When I create a new plain recipe
        And I update dataset recipe to the new recipe


    @pipelines.delete
    @testrail-C4529141
    Scenario: pipeline re-complete status for task
        When I create a package and service to pipeline
        And I create a pipeline dataset, task "annotation" and code nodes - repeatable "True"
        And I upload item in "0000000162.jpg" to pipe dataset
        Then I wait "7"
        And I update item status to "complete" with task id
        Then I wait "2"
        And I remove specific "complete" from item with task id
        Then I wait "2"
        And I update item status to "complete" with task id
        And I expect that pipeline execution has "4" success executions


    @pipelines.delete
    @testrail-C4529141
    Scenario: pipeline re-complete status for qa task
        When I create a package and service to pipeline
        And I create a pipeline dataset, task "qa" and code nodes - repeatable "True"
        And I upload item in "0000000162.jpg" to pipe dataset
        Then I wait "7"
        And I update item status to "approve" with task id
        Then I wait "2"
        And I remove specific "approve" from item with task id
        Then I wait "2"
        And I update item status to "approve" with task id
        And I expect that pipeline execution has "4" success executions


    @pipelines.delete
    @testrail-C4529141
    Scenario: pipeline re-complete status for repeatable false task
        When I create a package and service to pipeline
        And I create a pipeline dataset, task "annotation" and code nodes - repeatable "False"
        And I upload item in "0000000162.jpg" to pipe dataset
        Then I wait "7"
        And I update item status to "complete" with task id
        Then I wait "2"
        And I remove specific "complete" from item with task id
        Then I wait "2"
        And I update item status to "complete" with task id
        And I expect that pipeline execution has "3" success executions
