Feature: Compute archive testing

  Background: Initiate Platform Interface and create a project
    Given Platform Interface is initialized as dlp and Environment is set according to git branch
    And I create a project by the name of "compute_archive"


  @DAT-86651
  @restore_json_file
  @compute_serviceDriver.delete
  Scenario: SDK Test Compute archived - Create compute with the same name as archived compute Should success
    Given I fetch the compute from "computes/base_compute.json" file and update compute with params "True"
      | key           | value |
      | config.status | ready |
    When I try to create the compute from context.original_path
    Then I able to delete compute
    When I try to create the compute from context.original_path
    Then I validate no error in context
    When I get compute from the compute list by the name