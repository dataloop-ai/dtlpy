Feature: DPK with dependencies

  Background:
    Given Platform Interface is initialized as dlp and Environment is set according to git branch
    And I create a project by the name of "dpk_dependency_1"

  @DAT-69194
  Scenario: DPK with dependencies App 'usedBy' refs cases - Install and Uninstall
    Given I publish a pipeline node dpk from file "apps/app_scope_node.json" and with code path "move_item"
    When I install the app
    Given I fetch the dpk from 'apps/dependencies/solution_default.json' file
    When I add dependency to the dpk with params
      | key  | value                      |
      | name | context.published_dpk.name |
    And I publish a dpk to the platform
    And I install the app
    Then I validate app dependencies have "usedBy" relation refs "only"
    When I uninstall the app
    Then I validate app dependencies not have "usedBy" relation refs
    When I uninstall the app

  @DAT-69195
  Scenario: DPK with dependencies App clean-up refs cases - Uninstall and remove dpk
    Given I publish a pipeline node dpk from file "apps/app_scope_node.json" and with code path "move_item"
    And I fetch the dpk from 'apps/dependencies/solution_default.json' file
    When I add dependency to the dpk with params
      | key  | value                      |
      | name | context.published_dpk.name |
    And I publish a dpk to the platform
    Then I validate dpk dependencies have "usedBy" relation refs
    When I install the app
    Then I validate app dependencies have "createdBy" relation refs
    And I validate app dependencies have "usedBy" relation refs
    When I uninstall the app
    Then I validate app dependencies not installed
    When I delete published_dpk
    Then I validate dpk dependencies not have "usedBy" relation refs

