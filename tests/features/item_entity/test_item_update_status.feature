Feature: Item Entity update item status

  Background: Initiate Platform Interface and create a project
    Given Platform Interface is initialized as dlp and Environment is set according to git branch
    And There is a project by the name of "item_update_status"
    And I create a dataset with a random name
    And There are items, path = "filters/image.jpg"
      | annotated_type={"box": 3, "polygon": 3} | metadata={"user.good": 3, "user.bad": 3} |
    And I save dataset items to context

  @testrail-C4525318
  Scenario: Update default status on items in task
    When I create Task
      | task_name=min_params | due_date=auto | assignee_ids=auto |
    Then I receive a task entity
    When I update items status to default task actions
    Then I validate default items status in task

  @testrail-C4525318
  Scenario: Update default status on items in second task with task id
    When I create Task
      | task_name=min_params | due_date=auto | assignee_ids=auto |
    Then I receive a task entity
    When I update items status to default task actions with task id
    Then I validate default items status in task


  @testrail-C4525318
  Scenario: Update Custom status on items in task
    When I create Task
      | task_name=min_params | due_date=auto | assignee_ids=auto | available_actions=fix-label fix-ann fix-cor |
    Then I receive a task entity
    When I update items status to custom task actions "fix-label" "fix-ann" "fix-cor"
    Then I validate items status in task
#
#
#  @testrail-C4523167
#  Scenario: Update default status on items in qa task
#    When I create Task
#      | task_name=min_params | due_date=auto | assignee_ids=auto |
#    Then I receive a task entity
#    When I update items status to default task actions
#    When I update items status to default qa task actions
#    Then I validate default items status in qa task
#
#
#  @testrail-C4523167
#  Scenario: Update custom status on items in qa task
#    When I create Task
#      | task_name=min_params | due_date=auto | assignee_ids=auto |
#    Then I receive a task entity
#    When I update items status to default task actions
#    When I update items status to default qa task actions
#    Then I validate custom items status in qa task



