@rc_only
Feature: Service status testing

  Background: Initiate Platform Interface and create a project
    Given Platform Interface is initialized as dlp and Environment is set according to git branch
    And I create a project by the name of "services-status"

  @DAT-81805
  Scenario: Get service status from different drivers - Should be able to get services instances
    Given I create pipeline from json in path "pipelines_json/pipeline_service_status.json"
    And I install pipeline in context
    When I get service by name "run-1"
    Then I validate service has "1" instance up and replicaId include service name "True"
    When I get service by name "run-2"
    Then I validate service has "1" instance up and replicaId include service name "True" num_try 3

