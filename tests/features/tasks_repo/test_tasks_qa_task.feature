Feature: Tasks repository create qa task method testing

    Background: Initiate Platform Interface and create a project
        Given Platform Interface is initialized as dlp and Environment is set according to git branch
        And I create a project by the name of "tasks_create_qa"
        And I create a dataset with a random name
        And There are items, path = "filters/image.jpg"
            |annotated_type={"box": 3, "polygon": 3}|metadata={"user.good": 3, "user.bad": 3}|

    @testrail-C4523171
    Scenario: Create
        When I create Task
            | task_name=qa_test | due_date=auto | assignee_ids=auto | filters={"filter": {"$and": [{"hidden": false}, {"type": "file"}, {"annotated": true}]}} |
        And I update items status to default task actions
        And I create a qa task
            | due_date=auto | assignee_ids=auto |
        Then I receive a qa task object
        And Qa task is properly made
        And Task has the correct attributes for type "qa"

    @testrail-C4523171
    Scenario: Create - qa task with metadata
        Given I save dataset items to context
        When I create Task
            | task_name=metadata_task | assignee_ids=auto | metadata={"key": "value"} | items=3 |
        And I update items status to default task actions
        And I create a qa task
            | assignee_ids=auto | metadata={"key": "qa_value"} |
        Then I receive a qa task object
        And Qa task is properly made
        And Task has the correct attributes for type "qa"
