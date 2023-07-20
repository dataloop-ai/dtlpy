#@qa-nightly
#@bot.create
#Feature: Executions repository create service testing
#
#  Background: Initiate Platform Interface and create a project
#    Given Platform Interface is initialized as dlp and Environment is set according to git branch
#    And I create a project by the name of "execution_create"
#    And I create a dataset with a random name
#
#  @services.delete
#  @packages.delete
#  @DAT-46784
#  Scenario: Init error should raise notification
#    Given There is a package (pushed from "faas/importError") by the name of "import-error"
#    And There is a service by the name of "import-error" with module name "default_module" saved to context "service"
#    And I upload item in "0000000162.jpg" to dataset
#    When I create an execution with "inputs"
#      | sync=False | inputs=Item |
#    Then I receive "RequirementsError" notification
#    And Service is deactivated by system
