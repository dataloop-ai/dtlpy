Feature: Tasks repository add/get items method testing

    Background: Initiate Platform Interface and create a project
        Given Platform Interface is initialized as dlp and Environment is set according to git branch
        And I create a project by the name of "tasks_get_add_items"
        And I create a dataset with a random name
        And There are items, path = "filters/image.jpg"
            |annotated_type={"box": 3, "polygon": 3}|metadata={"user.good": 3, "user.bad": 3}|
        When Add Members "annotator1@dataloop.ai" as "annotator"
        And Add Members "annotator2@dataloop.ai" as "annotator"

    @testrail-C4523166
    @DAT-46621
    Scenario: Get items - by name
        When I create Task
            | task_name=min_params | due_date=auto | assignee_ids=auto |
        And I get Task items by "name"
        Then I receive task items list of "12" items

    @testrail-C4523166
    @DAT-46621
    Scenario: Get items - by id
        When I create Task
            | task_name=min_params | due_date=auto | assignee_ids=auto |
        And I get Task items by "id"
        Then I receive task items list of "12" items

    @testrail-C4523166
    @DAT-46621
    Scenario: Add items
      When I create Task
          | task_name=min_params | due_date=auto | assignee_ids=auto | filters={"filter": {"$and": [{"hidden": false}, {"type": "file"}, {"annotated": true}]}} |
      And I add items to task
          | task_id=auto | filters={"filter": {"$and": [{"hidden": false}, {"type": "file"}, {"annotated": false}]}} | assignee_ids=auto |
      And I get Task items by "id"
      Then I receive task items list of "12" items
