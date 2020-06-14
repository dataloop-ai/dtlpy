Feature: Assignments repository create method testing

    Background: Initiate Platform Interface and create a project
        Given Platform Interface is initialized as dlp and Environment is set according to git branch
        And There is a project by the name of "assignments_create"
        And I create a dataset with a random name
        And There are items, path = "filters/image.jpg"
            |annotated_type={"box": 3, "polygon": 3}|metadata={"user.good": 3, "user.bad": 3}|
        And I save dataset items to context

    Scenario: Create - minimum params
        When I create Task
            | task_name=min_params | due_date=auto |  assignee_ids=annotator1@dataloop.ai | items=3 |
        And I create an Assignment from "task" entity
            | assignee_id=annotator2@dataloop.ai | items=3 |
        Then I receive an assignment entity
        And Assignment has the correct attributes

    Scenario: Create - maximum params - filters
        When I create Task
            | task_name=min_params | due_date=auto |  assignee_ids=annotator1@dataloop.ai | filters={"annotated": true} |
        When I create an Assignment from "task" entity
            | assignee_id=annotator2@dataloop.ai | filters={"metadata":{"user.good": 3, "user.bad": 3}} | items=None |
        Then I receive an assignment entity
        And Assignment has the correct attributes

    Scenario: Create - maximum params - items
        When I create Task
            | task_name=min_params | due_date=auto |  assignee_ids=annotator1@dataloop.ai | items=3 |
        And I create an Assignment from "task" entity
            | assignee_id=annotator3@dataloop.ai | filters=None | items=3 |
        Then I receive an assignment entity
        And Assignment has the correct attributes