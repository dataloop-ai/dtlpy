Feature: Assignments repository redistribute method testing

    Background: Initiate Platform Interface and create a project
        Given Platform Interface is initialized as dlp and Environment is set according to git branch
        And I create a project by the name of "assignments_redistribute"
        And I create a dataset with a random name
        And There are items, path = "filters/image.jpg"
            |annotated_type={"box": 3, "polygon": 3}|metadata={"user.good": 3, "user.bad": 3}|
        When Add Members "annotator1@dataloop.ai" as "annotator"
        And Add Members "annotator2@dataloop.ai" as "annotator"
        And Add Members "annotator3@dataloop.ai" as "annotator"
        And Add Members "annotator4@dataloop.ai" as "annotator"
        And I create Task
            | task_name=redistribute| due_date=auto | assignee_ids=auto |
        And I get the first assignment

    @testrail-C4523060
    @DAT-46467
    Scenario: redistribute
        When I redistribute assignment to "annotator3@dataloop.ai,annotator4@dataloop.ai"
        Then Assignments was redistributed to "annotator3@dataloop.ai,annotator4@dataloop.ai"
