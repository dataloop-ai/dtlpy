Feature: Tasks repository create method testing

  Background: Initiate Platform Interface and create a project
    Given Platform Interface is initialized as dlp and Environment is set according to git branch
    And I create a project by the name of "tasks_create"
    And I create a dataset with a random name
    And There are items, path = "filters/image.jpg"
      | annotated_type={"box": 3, "polygon": 3} | metadata={"user.good": 3, "user.bad": 3} |
    And I save dataset items to context

   @testrail-C4523167
   Scenario: Create - minimum params
       When I create Task
           | task_name=min_params | due_date=auto | assignee_ids=auto |
       Then I receive a task entity
       And Task has the correct attributes for type "annotation"

  @testrail-C4523167
  Scenario: Create - maximum params - filters
    When I create Task
      | task_name=filters_task | due_date=auto | assignee_ids=auto | workload=None | dataset=auto | task_owner=auto | task_type=annotation | task_parent_id=None | project_id=auto | recipe_id=auto | assignments_ids=None | metadata={"key": "value"} | filters={"filter": {"$and": [{"hidden": false}, {"type": "file"}],"$or": [{"metadata": {"user.good": true}},{"metadata": {"user.bad": true}}]}} | items=None |
    Then I receive a task entity
    And Task has the correct attributes for type "annotation"

  @testrail-C4523167
  Scenario: Create - maximum params - items
    When I create Task
      | task_name=items_task | due_date=auto | assignee_ids=None | workload=auto | dataset=auto | task_owner=auto | task_type=annotation | task_parent_id=None | project_id=auto | recipe_id=auto | assignments_ids=None | metadata={"key": "value"} | filters=None | items=3 |
    Then I receive a task entity
    And Task has the correct attributes for type "annotation"


  @testrail-C4523167
  Scenario: Create - task with metadata
    When I create Task
      | task_name=metadata_task | assignee_ids=auto | metadata={"key": "value"} | items=3 |
    Then I receive a task entity
    And Task has the correct attributes for type "annotation"