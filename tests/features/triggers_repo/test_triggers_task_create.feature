#@bot.create
#Feature: Triggers repository create service testing
#
#    Background: Initiate Platform Interface and create a project
#        Given Platform Interface is initialized as dlp and Environment is set according to git branch
#        And I create a project by the name of "triggers_create"
#        And I create a dataset with a random name
#
#    @services.delete
#    @packages.delete
#    @testrail-C4525050
#    Scenario: Created Task Trigger
#        Given There is a package (pushed from "triggers/task") by the name of "triggers-create"
#        And There is a service by the name of "triggers-create" with module name "default_module" saved to context "service"
#        When I upload item in "0000000162.jpg" to dataset
#        And I create a trigger
#            |name=triggers-create|filters=None|resource=Task|action=Created|active=True|executionMode=Once|
#        Then I receive a Trigger entity
#        When I create Task
#            | task_name=default_name | due_date=auto | assignee_ids=annotator1@dataloop.ai |
#        Then I wait "7"
#        And Service was triggered on "task"