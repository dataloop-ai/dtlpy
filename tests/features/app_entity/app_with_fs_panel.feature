Feature: Testing App with fs served panel

  Background:
    Given Platform Interface is initialized as dlp and Environment is set according to git branch
    And I create a project by the name of "app-with-fs-panel"

  @DAT-80890
  @restore_json_file
  Scenario: Create and update app with FS panel
    Given I have an app with a filesystem panel in path "apps/filesystem_panel"
    When I fetch the panel
    Then I should find the sdk version from the computeConfig in the panel
    And no services deployed in the project
    Given I update the panel with a new sdk version
    When I fetch the panel
    Then I should find the sdk version from the computeConfig in the panel
    And no services deployed in the project
    Then I uninstall the app


  @DAT-83973
  @restore_json_file
  Scenario: Create app with FS panel - Deactivate and active the app Should work
    Given I have an app with a filesystem panel in path "apps/filesystem_panel"
    When I fetch the panel
    Then I should find the sdk version from the computeConfig in the panel
    When I pause the app
    Then The deactivation should succeed
    When I resume the app
    Then The activation should succeed
    Then I should find the sdk version from the computeConfig in the panel
    Then I uninstall the app


  @DAT-84375
  @pipelines.delete
  @restore_json_file
  Scenario: Create pipeline app with FS panel - Start pipeline should success
    Given I have an app with a filesystem panel in path "apps/pipeline_panel"
    When I fetch the panel
    Then I should find the sdk version from the computeConfig in the panel
    Given I create pipeline from json in path "pipelines_json/panel_node_fs.json"
    When I install pipeline in context
    Then Pipeline status is "Installed"
