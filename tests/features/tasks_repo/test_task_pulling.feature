Feature: Tasks repository create pulling task

  Background: Initiate Platform Interface and create a project
    Given Platform Interface is initialized as dlp and Environment is set according to git branch
    And I create a project by the name of "tasks_pulling"
    And I create a dataset with a random name
    And There are items, path = "filters/image.jpg"
      | annotated_type={"box": 3, "polygon": 3} | metadata={"user.good": 3, "user.bad": 3} |
    And I save dataset items to context

   @testrail-C4533548
   Scenario: Create - pulling task
       When I create Task
           | task_name=pulling_task | due_date=auto | batch_size=3 | allowed_assignees=auto | max_batch_workload=5 |
       Then I receive a task entity
       And Task has the correct attributes for type "annotation"