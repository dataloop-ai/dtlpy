Feature: Tasks repository create method testing

    Background: Initiate Platform Interface and create a project
        Given Platform Interface is initialized as dlp and Environment is set according to git branch
        And There is a project by the name of "tasks_create"
        And I create a dataset with a random name
        And There are items, path = "filters/image.jpg"
            |annotated_type={"box": 3, "polygon": 3}|metadata={"user.good": 3, "user.bad": 3}|
        And I save dataset items to context

    Scenario: Create - minimum params
        When I create Task
            | task_name=min_params | due_date=auto | assignee_ids=auto |
        Then I receive a task entity
        And Task has the correct attributes

    Scenario: Create - maximum params - filters
        When I create Task
            | task_name=filters_task | due_date=auto | assignee_ids=auto | workload=None | dataset=auto | task_owner=auto | status=open | task_type=annotation | task_parent_id=None | project_id=auto | recipe_id=auto | assignments_ids=None | metadata={"key": "value"} | filters={"metadata":{"user.good": 3, "user.bad": 3}} | items=None |
        Then I receive a task entity
        And Task has the correct attributes

    Scenario: Create - maximum params - items
        When I create Task
            | task_name=items_task | due_date=auto | assignee_ids=None | workload=auto | dataset=auto | task_owner=auto | status=close | task_type=annotation | task_parent_id=None | project_id=auto | recipe_id=auto | assignments_ids=None | metadata={"key": "value"} | filters=None | items=3 |
        Then I receive a task entity
        And Task has the correct attributes