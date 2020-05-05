Feature: Assignments repository reassign method testing

    Background: Initiate Platform Interface and create a project
        Given Platform Interface is initialized as dlp and Environment is set according to git branch
        And There is a project by the name of "assignments_reassign"
        And I create a dataset with a random name
        And There are items, path = "filters/image.jpg"
            |annotated_type={"box": 3, "polygon": 3}|metadata={"user.good": 3, "user.bad": 3}|
        When I create Task
            | task_name=reassign | due_date=auto | assignee_ids=auto |
        And I create an Assignment from "task" entity
            | assignment_name=reassign | assignee_id=annotator1@dataloop.ai | items=3 |

    Scenario: Reassign
        When I reassign assignment to "new_annotator@dataloop.ai"
        Then Assignments was reassigned to "new_annotator@dataloop.ai"