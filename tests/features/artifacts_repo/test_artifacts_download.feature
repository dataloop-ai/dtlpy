@bot.create
Feature: Artifacts repository get artifact testing

  Background: Initiate Platform Interface and create a project
    Given Platform Interface is initialized as dlp and Environment is set according to git branch
    And There is a project by the name of "test_artifacts_upload"
    And Directory "artifacts_upload" is empty
    When I generate package by the name of "test_package" to "artifacts_upload"
    Given Context "artifact_filepath" is "artifacts_repo/artifact_item.jpg"
    And Directory "artifacts_upload" is empty
    When I generate package by the name of "test-package" to "artifacts_upload"
    And I push "first" package
      | codebase_id=None | package_name=test-package | src_path=artifacts_upload | inputs=None | outputs=None | modules=None |

  @packages.delete
  Scenario: Download by artifact name - item
    When I upload "1" artifacts to "package"
    And I download artifact by "name"
    Then Artifact "item" was downloaded successfully

  @packages.delete
  Scenario: Download by artifact id - item
    When I upload "1" artifacts to "package"
    And I download artifact by "id"
    Then Artifact "item" was downloaded successfully

  @packages.delete
  Scenario: Download by artifact id - folder
    Given Context "artifact_filepath" is "artifacts_repo/artifact_folder"
    When I upload "1" artifacts to "package"
    And I download artifact by "id"
    Then Artifact "folder" was downloaded successfully

  @packages.delete
  Scenario: Download with package name - item
    When I upload "1" artifacts to "package"
    And I download artifact by "package_name"
    Then Artifact "item" was downloaded successfully

  @packages.delete
  @services.delete
  Scenario: Download with execution id
    Given There is a service by the name of "artifacts-upload" with module name "default_module" saved to context "service"
    And Context has attribute execution_id = True
    And I create a dataset with a random name
    And Item in path "0000000162.jpg" is uploaded to "Dataset"
    When I create an execution with "Item"
      |sync=False|inputs=Item|
    And I upload "1" artifacts to "execution"
    And I get artifact by "execution_id"
    And I download artifact by "execution_id"
    Then Artifact "item" was downloaded successfully