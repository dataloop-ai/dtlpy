@ATP @AIRGAPPED @ATPNONMODEL
Feature: Workforce Flow Testing

  Background: Initiate Platform Interface and create a projects and datasets
    Given Platform Interface is initialized as dlp and Environment is set according to git branch


  @DAT-79630
  Scenario: Workforce flow
    Given I create "project" name "WorkforceProject"
    Given I create "dataset" name "WorkforceDataset"
    When Add Members "owner@dataloop.ai" as "engineer"
    And Add Members "annotator1@dataloop.ai" as "annotationManager"
    And Add Members "annotator2@dataloop.ai" as "annotator"
    Given There are "5" items
    And Dataset has ontology
    And Classes in file: "classes_new.json" are uploaded to test Dataset
    When I add "checkbox" attribute to ontology
      | key=CheckBox | title=test1 | values=['a','b','c'] | scope=['Person'] | optional=False |
    Then I validate attribute "checkbox" added to ontology
    When I add "radio_button" attribute to ontology
      | key=RadioButton | title=test2 | values=['a','b','c'] | scope=all |
    Then I validate attribute "radio_button" added to ontology
    When I add "slider" attribute to ontology
      | key=Slider | title=test3 | scope=all | attribute_range=0,10,1 |
    Then I validate attribute "slider" added to ontology
    When I add "yes_no" attribute to ontology
      | key=YesNo | title=test4 | scope=all |
    Then I validate attribute "yes_no" added to ontology
    When I add "free_text" attribute to ontology
      | key=FreeText | title=test5 | scope=all |
    Then I validate attribute "free_text" added to ontology
    When I create Task
      | task_name=Task_1 | due_date=auto | assignee_ids=auto | task_owner=auto | workload=80,20 |
    When I validate "open" status on a "task"
    When I update task name "distribution_task"
    When I update task owner "annotator1@dataloop.ai"
    When I update task due_date 1917082584000
    When I update task priority 1
    Then I verify task "name" = "distribution_task"
    Then I verify task "task_owner" = "annotator1@dataloop.ai"
    Then I verify task "due_date" = "1917082584000"
    Then I verify task "priority" = "1"
    When I get assignment from task with assignee "annotator1@dataloop.ai"
    When I reassign assignment to "annotator2@dataloop.ai"
    Then Assignments was reassigned to "annotator2@dataloop.ai"
    When I get assignment from task
    When I redistribute assignment to "annotator1@dataloop.ai,annotator2@dataloop.ai"
    Then Assignments was redistributed to "annotator1@dataloop.ai,annotator2@dataloop.ai"
    When I get assignment from task
    When I upload "box" annotation with "Person" label
    When I set an issue to the annotation
    Then annotation status is "issue"
    When I update annotation status to "review"
    Then annotation status is "review"
    When I update annotation status to "approved"
    Then annotation status is "approved"
    When I update annotation status to "clear"
    Then annotation status is "clear"
    When I complete all items in task except for discarded items
    Then I validate "5" completed and "0" discarded items
    When I validate "completed" status on a "task"
    When I update annotation status to "approved"
    When I validate "completed" status on a "task"
    When I "clear" the "complete" status of the item on the task
    Then I validate "4" completed and "0" discarded items
    When I validate "open" status on a "task"
    When I "add" the "discard" status of the item on the task
    Then I validate "4" completed and "1" discarded items
    When I validate "completed" status on a "task"
    When I "clear" the "discard" status of the item on the task
    Then I validate "4" completed and "0" discarded items
    When I create a qa task
      | due_date=auto | assignee_ids=auto |
    When I get item from task
    When I "add" the "discard" status of the item on the QA task
    When I approve all items in task except for discarded items
    Then I validate "3" approved and "1" discarded items
    When I validate "completed" status on a "qa_task"
    When I "clear" the "discard" status of the item on the QA task
    Then I validate "3" approved and "0" discarded items
    When I validate "open" status on a "qa_task"
    When I "add" the "approve" status of the item on the QA task
    Then I validate "4" approved and "0" discarded items
    When I validate "completed" status on a "qa_task"
    When I delete qa_task by "object"
    When I delete task by "object"
    When I create Task
      | task_name=pulling_task | due_date=auto | assignee_ids=annotator1@dataloop.ai | task_owner=auto | batch_size=3 | max_batch_workload=5 |
