Feature: Task repository Context testing

    Background: Initiate Platform Interface and create a projects and datasets
        Given Platform Interface is initialized as dlp and Environment is set according to git branch
        And I create projects by the name of "project1 project2"
        And I create datasets by the name of "dataset1 dataset2"
        And I upload items in "0000000162.jpg" to datasets
        When Add Members "annotator1@dataloop.ai" as "annotator" to project 1
        And Add Members "annotator2@dataloop.ai" as "annotator" to project 1
        Given I create task belong to dataset 1
            | task_name=context_task_test | due_date=auto | assignee_ids=auto |

    @testrail-C4523172
    @DAT-46627
    Scenario: Get Task from the Project it belong to
        When I get the task from project number 1
        Then task Project_id is equal to project 1 id
        And task Project.id is equal to project 1 id
        And task dataset_id is equal to dataset 1 id
        And task dataset.id is equal to dataset 1 id

    @testrail-C4523172
    @DAT-46627
    Scenario: Get Task from the Project it is not belong to
        When I get the task from project number 2
        Then task Project_id is equal to project 1 id
        And task Project.id is equal to project 1 id
        And task dataset_id is equal to dataset 1 id
        And task dataset.id is equal to dataset 1 id

    @testrail-C4523172
    @DAT-46627
    Scenario: Get Task from the Dataset it belong to
        When I get the task from dataset number 1
        Then task Project_id is equal to project 1 id
        And task Project.id is equal to project 1 id
        And task dataset_id is equal to dataset 1 id
        And task dataset.id is equal to dataset 1 id

        @testrail-C4523172
        @DAT-46627
        Scenario: Get Task from the Dataset it not belong to
          When I get the task from dataset number 2
          Then task Project_id is equal to project 1 id
          And task Project.id is equal to project 1 id
          And task dataset_id is equal to dataset 1 id
          And task dataset.id is equal to dataset 1 id
