Feature: Tasks assignments

  Background: Initiate Platform Interface and create a project
    Given Platform Interface is initialized as dlp and Environment is set according to git branch
    And I create a project by the name of "tasks_test"
    And I create a dataset with a random name
    And There are items, path = "filters/image.jpg"
      | metadata={"user.good": 3, "user.bad": 3} |
    And I save dataset items to context
    When Add Members "annotator1@dataloop.ai" as "annotator"
    And Add Members "annotator2@dataloop.ai" as "annotator"

  @DAT-69267
  Scenario: task without batchNode - Should delete empty assignments
    When I create Task
      | task_name=batchNode | assignee_ids=auto | items=None |
    Then I receive a task entity
    When I add items to task
      | task_id=auto | filters={"filter": {"$and": [{"hidden": false}, {"type": "file"}, {"annotated": false}]}} | assignee_ids=auto |
    And I remove items from task
      | task_id=auto | filters={"filter": {"$and": [{"hidden": false}, {"type": "file"}, {"annotated": false}]}} |
    Then Task has "0" assignments

  @DAT-57964
  Scenario: task with batchNode - Shouldn't delete empty assignments
    When I create Task
      | task_name=batchNode | assignee_ids=auto | metadata={"type": "batchNode"} | items=None |
    Then I receive a task entity
    When I add items to task
      | task_id=auto | filters={"filter": {"$and": [{"hidden": false}, {"type": "file"}, {"annotated": false}]}} | assignee_ids=auto |
    And I remove items from task
      | task_id=auto | filters={"filter": {"$and": [{"hidden": false}, {"type": "file"}, {"annotated": false}]}} |
    Then Task has "2" assignments