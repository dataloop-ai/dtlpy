@bot.create
Feature: Artifacts repository get artifact testing

  Background: Initiate Platform Interface and create a project
    Given Platform Interface is initialized as dlp and Environment is set according to git branch
    And I create a project by the name of "test_artifacts_upload"
    And Directory "artifacts_upload" is empty
    When I generate package by the name of "test_package" to "artifacts_upload"
    Given Context "artifact_filepath" is "artifacts_repo/artifact_item.jpg"
    And Directory "artifacts_upload" is empty
    When I generate package by the name of "test-package" to "artifacts_upload"
    And I push "first" package
      | codebase_id=None | package_name=test-package | src_path=artifacts_upload | inputs=None | outputs=None | modules=None |

  @packages.delete
  @testrail-C4523049
  @DAT-46456
  Scenario: Delete by name - item
    When I upload "1" artifacts to "package"
    When I delete artifact by "name"
    Then Artifact does not exist "name"

  @packages.delete
  @testrail-C4523049
  @DAT-46456
  Scenario: Delete with package  - item
    When I upload "1" artifacts to "package"
    When I delete artifact by "id"
    Then Artifact does not exist "id"

  @packages.delete
  @testrail-C4523049
  @DAT-46456
  Scenario: Delete with package name
    When I upload "1" artifacts to "package"
    When I delete artifact by "package_name"
    Then Artifact does not exist "package_name"

  @packages.delete
  @services.delete
  @testrail-C4523049
  @DAT-46456
  Scenario: Delete with execution
    Given There is a service by the name of "artifacts-upload" with module name "default_module" saved to context "service"
    And I create a dataset with a random name
    And Item in path "0000000162.jpg" is uploaded to "Dataset"
    When I create an execution with "Item"
      |sync=False|inputs=Item|
    And I upload "1" artifacts to "execution"
    When I delete artifact by "execution_id"
    Then Artifact does not exist "execution_id"
