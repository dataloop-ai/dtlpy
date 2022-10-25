@bot.create
Feature: Triggers repository types - itemStatus

    Background: Initiate Platform Interface and create a project
        Given Platform Interface is initialized as dlp and Environment is set according to git branch
        And I create a project by the name of "triggers_update"
        And I create a dataset with a random name

    @services.delete
    @packages.delete
    @testrail-C4525051
    Scenario: Update ItemStatus Trigger once
        Given There is a package (pushed from "triggers/item") by the name of "triggers-update"
        And There is a service by the name of "triggers-update" with module name "default_module" saved to context "service"
        When I upload item in "0000000162.jpg" to dataset
        When I create a trigger
            |name=triggers-update|filters=None|resource=ItemStatus|action=Updated|active=True|executionMode=Once|
        Then I receive a Trigger entity
        When I create Task
            | task_name=min_params | due_date=auto | assignee_ids=auto |
        Then I receive a task entity
        When I update items status to default task actions
        Then Service was triggered on "item"

    @services.delete
    @packages.delete
    @testrail-C4525051
    Scenario: Update ItemStatus Trigger once
        Given There is a package (pushed from "triggers/item") by the name of "triggers-update"
        And There is a service by the name of "triggers-update" with module name "default_module" saved to context "service"
        When I upload item in "0000000162.jpg" to dataset
        When I create a trigger
            |name=triggers-update|filters=None|resource=ItemStatus|action=Updated|active=True|executionMode=Always|
       Then I receive a Trigger entity
        When I create Task
            | task_name=min_params | due_date=auto | assignee_ids=auto |
        Then I receive a task entity
        When I update items status to default task actions
               Then I receive a Trigger entity
        When I create Task
            | task_name=min_params | due_date=auto | assignee_ids=auto |
        Then I receive a task entity
        When I update items status to default task actions with task id
        Then Service was triggered on "item" again
