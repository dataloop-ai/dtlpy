Feature: Executions load balancer test

  Background: Initiate Platform Interface and create a project
    Given Platform Interface is initialized as dlp and Environment is set according to git branch
    And I create a project by the name of "execution_create"

  @DAT-95899
  Scenario: Noisy neighbor service execution
    Given a service that run many executions
    Given a scaled up regular service
    When the regular service is executed while the noisy neighbor service is running
    Then the noisy neighbor service should not affect the regular service execution time