@bot.create
Feature: Triggers repository - Assignment input resource

  Background: Initiate Platform Interface and create a project
    Given Platform Interface is initialized as dlp and Environment is set according to git branch
    And I create a project by the name of "assignment_triggers"
    And I create a dataset with a random name
    When Add Members "annotator1@dataloop.ai" as "annotator"

  @services.delete
  @packages.delete
  @testrail-C4536678
  Scenario: Created Assignment Trigger action created once
    Given There is a package (pushed from "triggers/assignment") by the name of "triggers-assignment-once"
    And There is a service by the name of "triggers-assignment-once" with module name "default_module" saved to context "service"
    When I upload item in "0000000162.jpg" to dataset
    And I create a trigger
      | name=triggers-create | filters=None | resource=Assignment | action=Created | active=True | executionMode=Once |
    Then I receive a Trigger entity
    When I create Task
      | task_name=default_name | due_date=auto | assignee_ids=annotator1@dataloop.ai |
    Then I wait "5"
    When I get assignment from task
    And I update assignment name "name-updated"
    Then Service was triggered on "assignment"

  @services.delete
  @packages.delete
  @testrail-C4536678
  Scenario: Created Assignment Trigger action updated mode always
    Given There is a package (pushed from "triggers/assignment") by the name of "triggers-assignment-always"
    And There is a service by the name of "triggers-assignment-always" with module name "default_module" saved to context "service"
    When I upload item in "0000000162.jpg" to dataset
    And I create Task
      | task_name=default_name | due_date=auto | assignee_ids=annotator1@dataloop.ai |
    And I create a trigger
      | name=triggers-update | filters=None | resource=Assignment | action=Updated | active=True | executionMode=Always |
    Then I wait "5"
    When I get assignment from task
    And I update assignment name "assignment-updated"
    Then Service was triggered on "assignment"
    When I update assignment name "assignment-updated-again"
    Then Service was triggered on "assignment" again
