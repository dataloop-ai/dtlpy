Feature: DPK Pipeline template testing

  Background: Initiate Platform Interface and create a pipeline
    Given Platform Interface is initialized as dlp and Environment is set according to git branch
    And I create a project by the name of "update_dpk"


  @pipelines.delete
  @DAT-76220
  Scenario: update dpk attributes
    Given I create a dataset named "Upload-data"
    And I Add dataset to context.datasets
    And I create a dataset named "Ground-Truth"
    And I Add dataset to context.datasets
    When I fetch the dpk from 'apps/dpk_with_template_pipe.json' file
    And I publish a dpk to the platform
    And set context.published_dpk to context.dpk
    And i update the dpk attr "display_name" with value "newDisplayName"
    And i update the dpk attr "icon" with value "newIcon"
    And i update the dpk attr "scope" with value "public"
    And i update the dpk attr "attributes" with value "{'status': 'updated'}"
    And i update the dpk pipe template preview
    And i update the dpk
    Then I should see the dpk updated successfully


  @DAT-76902
  @rc_only
  Scenario: Try to update a public DPK - Should failed for regular users
    When I get global dpk by name "pipeline_template_1"
    And I try to update the dpk
    Then "Permission denied" in error message with status code "403"
