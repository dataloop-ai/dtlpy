Feature: Assignments repository delete method testing

    Background: Initiate Platform Interface and create a project
        Given Platform Interface is initialized as dlp and Environment is set according to git branch
        And There is a project by the name of "assignments_delete"
        And I create a dataset with a random name
        And There are items, path = "filters/image.jpg"
            |annotated_type={"box": 3, "polygon": 3}|metadata={"user.good": 3, "user.bad": 3}|
        And I save dataset items to context
        When I create Task
            | task_name=assignments_delete | due_date=auto | assignee_ids=assignee_id=annotator1@dataloop.ai | items=3 |
        And I get an Assignment

    Scenario: DELETE - id
        When I delete assignment by "id"
        Then Assignment was deleted

    Scenario: DELETE - name
        When I delete assignment by "name"
        Then Assignment was deleted