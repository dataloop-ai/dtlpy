@bot.create
Feature: Packages repository create slot testing

  Background: Initiate Platform Interface and create a project
    Given Platform Interface is initialized as dlp and Environment is set according to git branch
    And I create a project by the name of "test_ui_slot"
    And I create a dataset with a random name
    And There is a package (pushed from "services/item") by the name of "services-create"


  @services.delete
  @packages.delete
  @testrail-C4532930
  Scenario: Activate UI slot in service - Slot should create in settings
    When I create a service
      | service_name=services-create | package=services-create | revision=None | config=None | runtime=None |
    And I get package entity from service
    And I add UI slot to the package
    Then I validate slot is added to the package
    When I update service to latest package revision
    And I activate UI slot in service
    Then I get setting for context service


  @services.delete
  @packages.delete
  @testrail-C4532930
  Scenario: Update UI slot display_name Should updated in settings
    When I create a service
      | service_name=services-create | package=services-create | revision=None | config=None | runtime=None |
    And I get package entity from service
    And I add UI slot to the package
    When I update service to latest package revision
    And I activate UI slot in service
    And I update UI slot display_name to "new-ui-slot"
    And I update service to latest package revision
    Then I get setting for context service
    And I validate service UI slot is equal to settings


  @services.delete
  @packages.delete
  @testrail-C4532930
  Scenario: Update package and UI slot with new function Should updated in settings
    When I create a service
      | service_name=services-create | package=services-create | revision=None | config=None | runtime=None |
    And I get package entity from service
    And I add UI slot to the package
    And I update service to latest package revision
    And I activate UI slot in service
    And I add new function to package
    And I add new function to UI slot
    And I update service to latest package revision
    And I activate UI slot in service
    Then I get setting for context service
    And I validate service UI slot is equal to settings

