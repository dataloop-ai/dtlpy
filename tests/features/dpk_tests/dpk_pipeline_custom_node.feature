Feature: publish a dpk with pipeline Custom Node

  Background:
    Given Platform Interface is initialized as dlp and Environment is set according to git branch
    And I create a project by the name of "dpk-compare-model"

  @DAT-56172
  Scenario: Install dpk with specific dtlpy version - Service should be with the same version
    Given I fetch the dpk from 'apps/app_compare_models.json' file
    When I publish a dpk to the platform
    And I install the app
    And I wait "5"
    Given I create pipeline from json in path "pipelines_json/pipeline_compare_models_node.json"
    And I install pipeline in context
    When I wait "5"
    And I get service by name "compare-models-test"
    Then I validate service configuration in dpk is equal to service from app
