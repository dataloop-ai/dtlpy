Feature: Tasks repository priorities

    Background: Initiate Platform Interface and create a project
        Given Platform Interface is initialized as dlp and Environment is set according to git branch
        And I create a project by the name of "tasks_create"
        And I create a dataset with a random name
        And There are items, path = "filters/image.jpg"
            | annotated_type={"box": 3, "polygon": 3} | metadata={"user.good": 3, "user.bad": 3} |
        And I save dataset items to context

    @testrail-C4532755
    Scenario: Create - LOW priority task
        When I create Task with priority "TaskPriority.LOW"
        Then Task with priority "LOW" got created
        When I create Task with priority "TASK_PRIORITY_LOW"
        Then Task with priority "LOW" got created

    @testrail-C4532755
    Scenario: Create - MEDIUM priority task
        When I create Task with priority "TaskPriority.MEDIUM"
        Then Task with priority "MEDIUM" got created
        When I create Task with priority "TASK_PRIORITY_MEDIUM"
        Then Task with priority "MEDIUM" got created

    @testrail-C4532755
    Scenario: Create - HIGH priority task
        When I create Task with priority "TaskPriority.HIGH"
        Then Task with priority "HIGH" got created
        When I create Task with priority "TASK_PRIORITY_HIGH"
        Then Task with priority "HIGH" got created
