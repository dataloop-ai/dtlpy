@bot.create
Feature: Triggers repository create service testing - Task resource

  Background: Initiate Platform Interface and create a project
    Given Platform Interface is initialized as dlp and Environment is set according to git branch
    And I create a project by the name of "task_triggers"
    And I create a dataset with a random name
    When Add Members "annotator1@dataloop.ai" as "annotator"

  @services.delete
  @packages.delete
  @testrail-C4533676
  Scenario: Created Task Trigger action created once
    Given There is a package (pushed from "triggers/task") by the name of "triggers-task-once"
    And There is a service by the name of "triggers-task-once" with module name "default_module" saved to context "service"
    When I upload item in "0000000162.jpg" to dataset
    And I create a trigger
      | name=triggers-create | filters=None | resource=Task | action=Created | active=True | executionMode=Once |
    Then I receive a Trigger entity
    When I create Task
      | task_name=default_name | due_date=auto | assignee_ids=annotator1@dataloop.ai |
    Then I wait "7"
    And Service was triggered on "task"


  @services.delete
  @packages.delete
  @testrail-C4533676
  Scenario: Created Task Trigger action updated mode always
    Given There is a package (pushed from "triggers/task") by the name of "triggers-task-always"
    And There is a service by the name of "triggers-task-always" with module name "default_module" saved to context "service"
    When I create Task
      | task_name=default_name | due_date=auto | assignee_ids=annotator1@dataloop.ai |
    And I create a trigger
      | name=triggers-update | filters=None | resource=Task | action=Updated | active=True | executionMode=Always |
    And I update task name "Task-updated"
    Then Service was triggered on "task"
    When I update task name "Task-updated-again"
    Then Service was triggered on "task" again
