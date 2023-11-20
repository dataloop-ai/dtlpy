Feature: Tasks repository create qualification task

  Background: Initiate Platform Interface and create a project
    Given Platform Interface is initialized as dlp and Environment is set according to git branch
    And I create a project by the name of "tasks_consensus"
    And I create a dataset with a random name
    And There are "10" items
    And I save dataset items to context
    When Add Members "annotator1@dataloop.ai" as "annotator"
    And Add Members "annotator2@dataloop.ai" as "annotator"

  @DAT-50209
  Scenario: Create qualification task for 10 items - Should create task with 30 items (20 clones, 10 originals)
    When I create Task
      | task_name=min_params | due_date=auto | assignee_ids=auto | metadata={"system":{"consensusTaskType":"qualification"}} |
    Then I receive a task entity
    And Task has the correct attributes for type "annotation"
    And I expect Task created with "30" items