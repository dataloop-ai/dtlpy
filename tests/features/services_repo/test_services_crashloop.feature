@bot.create
Feature: Services repository crashloopbackoff

  Background: Initiate Platform Interface and create a project
    Given Platform Interface is initialized as dlp and Environment is set according to git branch
    And I create a project by the name of "services_crashloop"
    And I create a dataset with a random name

  @services.delete
  @packages.delete
  @DAT-52810
  Scenario: Service with one init error should not be deactivated
    Given I upload item in "0000000162.jpg" to dataset
    Given Service that restart once in init
    When service is deployed with num replicas > 0
    Then I receive "InitError" notification with resource "service.id"
    Then service should stay active


