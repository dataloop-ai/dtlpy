Feature: DPK with dependencies

  Background:
    Given Platform Interface is initialized as dlp and Environment is set according to git branch
    And I create a project by the name of "dpk_dependency_1"

  @DAT-69005
  Scenario: DPK with dependencies - App and apps should be deployed according to dependencies
    Given I publish a pipeline node dpk from file "apps/app_scope_node.json" and with code path "move_item"
    Given I publish a model dpk from file "model_dpk/modelsDpks.json" package "dummymodel"
    And I fetch the dpk from 'apps/dependencies/solution_default.json' file
    When I add dependency to the dpk with params
      | key  | value                          |
      | name | context.published_dpks[0].name |
    When I add dependency to the dpk with params
      | key  | value                          |
      | name | context.published_dpks[1].name |
    And I publish a dpk to the platform
    Then I validate dpk dependencies have "usedBy" relation refs
    When I install the app
    Then I validate app dependencies are installed
    And I validate app dependencies have "createdBy" relation refs
    And I validate app dependencies have "usedBy" relation refs

