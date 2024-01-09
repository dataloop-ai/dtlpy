Feature: publish a dpk with pipeline Custom Node

  Background:
    Given Platform Interface is initialized as dlp and Environment is set according to git branch
    And I create a project by the name of "dpk-scope-node"

  @DAT-62640
  Scenario: Install dpk with with scope nodes install service per node
    Given I fetch the dpk from 'apps/app_node_models.json' file
    When I publish a dpk to the platform
    And I install the app
    And I wait "5"
    Given I create pipeline from json in path "pipelines_json/pipeline_compare_app_node.json"
    And I install pipeline in context
    When I wait "5"
    And I list services in project
    Then I receive a Service list of "3" objects


  @DAT-62875
  Scenario: Install dpk with with scope node - Execution should be success
    Given I fetch the dpk from 'apps/app_scope_node.json' file
    And I create a dataset with a random name
    When I set code path "move_item" to context
    And I pack directory by name "move_item"
    And I add codebase to dpk
    And I publish a dpk to the platform
    And I install the app
    And I wait "5"
    Given I create pipeline from json in path "pipelines_json/pipeline_scope_node.json"
    And I install pipeline in context
    When I wait "5"
    And I upload item in "0000000162.jpg" to dataset
    Then I expect that pipeline execution has "1" success executions