Feature: Tasks repository delete method testing

  Background: Initiate Platform Interface and create a project
    Given Platform Interface is initialized as dlp and Environment is set according to git branch
    And I create a project by the name of "tasks_delete"
    And I create a dataset with a random name
    And There are items, path = "filters/image.jpg"
      | annotated_type={"box": 3, "polygon": 3} | metadata={"user.good": 3, "user.bad": 3} |

  @testrail-C4523168
  Scenario: Delete - by name
    When I create Task
      | task_name=min_params | due_date=auto | assignee_ids=auto |
    And I delete task by "name"
    Then Task has been deleted

  @testrail-C4523168
  Scenario: Delete - by id
    When I create Task
      | task_name=min_params | due_date=auto | assignee_ids=auto |
    And I delete task by "id"
    Then Task has been deleted


  @testrail-C4523168
  Scenario: Delete - by object
    When I create Task
      | task_name=min_params | due_date=auto | assignee_ids=auto |
    And I delete task by "object"
    Then Task has been deleted
