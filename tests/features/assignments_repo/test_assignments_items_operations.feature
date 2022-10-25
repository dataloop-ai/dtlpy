Feature: Assignments repository items operations method testing

    Background: Initiate Platform Interface and create a project
        Given Platform Interface is initialized as dlp and Environment is set according to git branch
        And I create a project by the name of "assignments_items_operations"
        And I create a dataset with a random name


    @testrail-C4523057
    Scenario: Get assignment items operation
        And There are items, path = "filters/image.jpg"
            |annotated_type={"box": 3, "polygon": 3}|metadata={"user.good": 3, "user.bad": 3}|
        And I save dataset items to context
        When I create Task
            | task_name=min_params | due_date=auto | assignee_ids=annotator1@dataloop.ai  | items=3 |
        And I get an Assignment

