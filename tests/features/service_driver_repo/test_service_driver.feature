Feature: Service driver testing

  Background: Initiate Platform Interface and create a project
    Given Platform Interface is initialized as dlp and Environment is set according to git branch
    And I create a project by the name of "service_driver_test"


  @DAT-86911
  @restore_json_file
  @compute_serviceDriver.delete
  Scenario: Create compute - Service driver should created before bootstrap
    Given I fetch the compute from "computes/base_compute.json" file and update compute with params "True"
      | key           | value |
      | config.status | ready |
    When I try to create the compute from context.original_path
    Then I validate compute service driver is "created"

  @DAT-87190
  @restore_json_file
  @compute_serviceDriver.delete
  Scenario: Create compute - Service driver should archived if compute is archived
    Given I fetch the compute from "computes/base_compute.json" file and update compute with params "True"
      | key           | value |
      | config.status | None  |
    When I try to create the compute from context.original_path
    And I get compute from the compute list by the name with archived "True"
    Then I validate compute service driver is "archived"
    And I get archived service driver