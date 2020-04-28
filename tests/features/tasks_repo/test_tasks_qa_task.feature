Feature: Tasks repository create qa task method testing

    Background: Initiate Platform Interface and create a project
        Given Platform Interface is initialized as dlp and Environment is set according to git branch
        And There is a project by the name of "tasks_create_qa"
        And I create a dataset with a random name
        And There are items, path = "filters/image.jpg"
            |annotated_type={"box": 3, "polygon": 3}|metadata={"user.good": 3, "user.bad": 3}|

    Scenario: Create
        When I create Task
            | task_name=qa_test | due_date=auto | assignee_ids=auto | filters={"filter": {"$and": [{"hidden": false}, {"type": "file"}, {"annotated": true}]}} |
        And I create a qa task
            | due_date=auto | assignee_ids=auto |
        Then I receive a qa task object
        And Qa task is properly made

