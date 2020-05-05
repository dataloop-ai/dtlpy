Feature: Assignments repository get method testing

    Background: Initiate Platform Interface and create a project
        Given Platform Interface is initialized as dlp and Environment is set according to git branch
        And There is a project by the name of "assignments_get"
        And I create a dataset with a random name
        And There are items, path = "filters/image.jpg"
            |annotated_type={"box": 3, "polygon": 3}|metadata={"user.good": 3, "user.bad": 3}|
        When I create Task
            | task_name=min_params | due_date=auto | assignee_ids=auto |
        And I create an Assignment from "task" entity
            | assignment_name=min_params | assignee_id=annotator1@dataloop.ai | items=3 |

    Scenario: GET - id
        When I get assignment by "id"
        Then I get an assignment entity
        And Assignment received equals assignment created

    Scenario: GET - name
        When I get assignment by "name"
        Then I get an assignment entity
        And Assignment received equals assignment created