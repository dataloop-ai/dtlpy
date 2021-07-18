@bot.create
Feature: Services repository logs testing

  Background: Initiate Platform Interface and create a project
    Given Platform Interface is initialized as dlp and Environment is set according to git branch
    And There is a project by the name of "services_log"
    And I create a dataset with a random name
    And There is a package (pushed from "services/item") by the name of "services-log"

  @services.delete
  @packages.delete
  Scenario: Log
    When I create a service
      | service_name=services-log | package=services-log | revision=None | config=None | runtime=None |
    Then I receive a Service entity
    And I upload an item by the name of "test_item.jpg"
    And I run a service execute for the item
    And Log "THIS LOG LINE SHOULD BE IN LOGS" is in service.log()

  @services.delete
  @packages.delete
  Scenario: Log init
    When I create a service with autoscaler
      | service_name=services-log-init | package=services-log-init | revision=None | config=None | runtime=None |
    Then I receive a Service entity
    And Log "THIS LOG LINE SHOULD BE IN LOGS" is in service.log()
