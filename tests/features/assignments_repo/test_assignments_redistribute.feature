Feature: Assignments repository redistribute method testing

    Background: Initiate Platform Interface and create a project
        Given Platform Interface is initialized as dlp and Environment is set according to git branch
        And There is a project by the name of "assignments_redistribute"
        And I create a dataset with a random name
        And There are items, path = "filters/image.jpg"
            |annotated_type={"box": 3, "polygon": 3}|metadata={"user.good": 3, "user.bad": 3}|
        When I create Task
            | task_name=redistribute| due_date=auto |
        And I create an Assignment from "task" entity
            | assignment_name=redistribute | assignee_id=annotator1@dataloop.ai | items=3 |

    Scenario: redistribute
        When I redistribute assignment to "annotator1,annotator2"
        Then Assignments was redistributed to "annotator1,annotator2"