#@qa-nightly
#@bot.create
#Feature: Executions repository create service testing
#
#  Background: Initiate Platform Interface and create a project
#    Given Platform Interface is initialized as dlp and Environment is set according to git branch
#    And I create a project by the name of "imagepullback_error"
#    And I create a dataset with a random name
#
#  @services.delete
#  @packages.delete
#  @DAT-46786
#  Scenario: Docker Image error should raise notification
#    Given There is a package (pushed from "faas/initError") by the name of "imagepullback-error"
#    And There is a service by the name of "imagepullback-error" with module name "default_module" saved to context "service"
#    And Service has wrong docker image
#    When Service minimum scale is "1"
#    Then I receive "ImagePullBackOff" notification with resource "service.id"
#    And Service is deactivated by system
