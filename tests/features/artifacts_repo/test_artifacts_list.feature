@bot.create
Feature: Artifacts repository list artifact testing

  Background: Initiate Platform Interface and create a project
    Given Platform Interface is initialized as dlp and Environment is set according to git branch
    And There is a project by the name of "test_artifacts_upload"
    And Directory "artifacts_upload" is empty
    When I generate package by the name of "test_package" to "artifacts_upload"
    Given Context "artifact_filepath" is "artifacts_repo/artifact_item.jpg"
    And Directory "artifacts_upload" is empty
    When I generate package by the name of "test_package" to "artifacts_upload"
    And I push "first" package
      | codebase_id=None | package_name=test_package | src_path=artifacts_upload | inputs=None | outputs=None | modules=no_input |

  @packages.delete
  Scenario: list package artifacts
    And I list Artifacts with "package_name"
    Then I receive artifacts list of "0" items
    When I upload "3" artifacts to "package"
    And I list Artifacts with "package_name"
    Then I receive artifacts list of "3" items

  @packages.delete
  @services.delete
  Scenario: Use with execution
    Given There is a service by the name of "artifacts-upload" with module name "default_module" saved to context "service"
    When I create an execution with "None"
      | sync=False |
    And I list Artifacts with "execution_id"
    Then I receive artifacts list of "0" items
    When I upload "3" artifacts to "execution"
    And I list Artifacts with "execution_id"
    Then I receive artifacts list of "3" items