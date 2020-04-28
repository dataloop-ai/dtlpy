Feature: Assignments repository items operations method testing

    Background: Initiate Platform Interface and create a project
        Given Platform Interface is initialized as dlp and Environment is set according to git branch
        And There is a project by the name of "assignments_items_operations"
        And I create a dataset with a random name
        And There are items, path = "filters/image.jpg"
            |annotated_type={"box": 3, "polygon": 3}|metadata={"user.good": 3, "user.bad": 3}|
        When I create Task
            | task_name=min_params | due_date=auto |
        And I create an Assignment from "task" entity
            | assignment_name=assignments_items_operations | assignee_id=annotator1@dataloop.ai | items=3 |

    Scenario: Get/delete/add items
        When I get assignment items
        Then I receive a list of "3" assignment items
        When I add "3" items to assignment
        And I get assignment items
        Then I receive a list of "6" assignment items
        When I delete all items from assignment
        And I get assignment items
        Then I receive a list of "0" assignment items
