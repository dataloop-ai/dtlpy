
Feature: Delete org

  Background: Initiate Platform Interface
    Given Platform Interface is initialized as dlp and Environment is set according to git branch
    And I log in as a "superuser"
    Given I create "org" name "org_to_delete"
    Given I create a project by the name of "org_to_delete_project"
    Given Add Members "user" as "owner"
    Given I update the project org
    And I log in as a "user"

  @DAT-37256
  Scenario: Delete org with FaaS services
    Given I create a dataset with a random name
    When I create a new plain recipe
    And I update dataset recipe to the new recipe
    And I log in as a "superuser"
    And I create a pipeline with code node
    And I delete the org
    Then Error message includes "Deleting the organization associated with your project cannot be done as long as there are FaaS services deployed in this project. To delete the organization, please delete all deployed FaaS services and try again."
