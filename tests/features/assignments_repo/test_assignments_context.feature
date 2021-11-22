Feature: Assignments repository Context testing

    Background: Initiate Platform Interface and create a projects and datasets
        Given Platform Interface is initialized as dlp and Environment is set according to git branch
        And I create projects by the name of "project1 project2"
        And I create datasets by the name of "dataset1 dataset2"
        And I set Dataset to Dataset 1
        And There are items, path = "filters/image.jpg"
            |annotated_type={"box": 3, "polygon": 3}|metadata={"user.good": 3, "user.bad": 3}|
        And I save dataset items to context
        When I create Task
            | task_name=min_params | due_date=auto | assignee_ids=auto | items=3 |
        And I append task to tasks
        And I get an Assignment

    @testrail-C4523054
    Scenario: Get Assignment from the Project it belong to
        When I get the assignment from project number 1
        Then assignment Project_id is equal to project 1 id
        And assignment Project.id is equal to project 1 id
        And assignment dataset_id is equal to dataset 1 id
        And assignment dataset.id is equal to dataset 1 id
        And assignment task_id is equal to task 1 id
        And assignment task.id is equal to task 1 id

    @testrail-C4523054
    Scenario: Get Assignment from the Project it not belong to
        When I get the assignment from project number 2
        Then assignment Project_id is equal to project 1 id
        And assignment Project.id is equal to project 1 id
        And assignment dataset_id is equal to dataset 1 id
        And assignment dataset.id is equal to dataset 1 id
        And assignment task_id is equal to task 1 id
        And assignment task.id is equal to task 1 id

    @testrail-C4523054
    Scenario: Get Assignment from the Dataset it belong to
        When I get the assignment from dataset number 1
        Then assignment Project_id is equal to project 1 id
        And assignment Project.id is equal to project 1 id
        And assignment dataset_id is equal to dataset 1 id
        And assignment dataset.id is equal to dataset 1 id
        And assignment task_id is equal to task 1 id
        And assignment task.id is equal to task 1 id

    @testrail-C4523054
    Scenario: Get Assignment from the Dataset it not belong to
        When I get the assignment from dataset number 2
        Then assignment Project_id is equal to project 1 id
        And assignment Project.id is equal to project 1 id
        And assignment dataset_id is equal to dataset 1 id
        And assignment dataset.id is equal to dataset 1 id
        And assignment task_id is equal to task 1 id
        And assignment task.id is equal to task 1 id

    @testrail-C4523054
    Scenario: Get Assignment from the Task it belong to
        Then assignment Project_id is equal to project 1 id
        And assignment Project.id is equal to project 1 id
        And assignment dataset_id is equal to dataset 1 id
        And assignment dataset.id is equal to dataset 1 id
        And assignment task_id is equal to task 1 id
        And assignment task.id is equal to task 1 id

    @testrail-C4523054
    Scenario: Get Assignment from the Task it not belong to
        Given  I set Dataset to Dataset 2
        And There are items, path = "filters/image.jpg"
            |annotated_type={"box": 3, "polygon": 3}|metadata={"user.good": 3, "user.bad": 3}|
        And I save dataset items to context
        When I create Task
            | task_name=min_params | due_date=auto | assignee_ids=auto | items=3 |
        And  I get Assignment by "id"
        Then assignment Project_id is equal to project 1 id
        And assignment Project.id is equal to project 1 id
        And assignment dataset_id is equal to dataset 1 id
        And assignment dataset.id is equal to dataset 1 id
        And assignment task_id is equal to task 1 id
        And assignment task.id is equal to task 1 id