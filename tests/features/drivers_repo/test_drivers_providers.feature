Feature: Drivers provider end point testing

  Background:
    Given Platform Interface is initialized as dlp and Environment is set according to git branch

  @DAT-85604
  Scenario: Get drivers by provider
    When I create a project by the name of "to-delete-test-project_create"
    When I get a project by the name of "to-delete-test-project_create"
    When I send "get" gen_request with "drivers_by_provider" params
    Then I validate attributes response in context.req