@bot.create
Feature: Artifacts repository get artifact testing

  Background: Initiate Platform Interface and create a project
    Given Platform Interface is initialized as dlp and Environment is set according to git branch
    And I create a project by the name of "test_artifacts_upload"
    And Directory "artifacts_upload" is empty
    When I generate package by the name of "test-package" to "artifacts_upload"
    Given Context "artifact_filepath" is "artifacts_repo/artifact_item.jpg"
    And Directory "artifacts_upload" is empty
    When I generate package by the name of "test-package" to "artifacts_upload"
    And I push "first" package
      | codebase_id=None | package_name=test-package | src_path=artifacts_upload | inputs=None | outputs=None | modules=None |

  @packages.delete
  @testrail-C4523051
  Scenario: Get by name - item
    When I upload "1" artifacts to "package"
    And I get artifact by "name"
    Then I receive an Artifact entity
    And Artifact received equals to the one uploaded

  @packages.delete
  @testrail-C4523051
  Scenario: Get by artifact name - non-existing
    When I upload "1" artifacts to "package"
    When I get artifact by "wrong_artifact_name"
    Then "NotFound" exception should be raised

  @packages.delete
  @testrail-C4523051
  Scenario: Get by package name - non-existing
    When I upload "1" artifacts to "package"
    When I get artifact by "wrong_package_name"
    Then "NotFound" exception should be raised

  @packages.delete
  @testrail-C4523051
  Scenario: Get by artifact id - non-existing
    When I upload "1" artifacts to "package"
    When I get artifact by "wrong_artifact_id"
    Then "BadRequest" exception should be raised

  @packages.delete
  @testrail-C4523051
  Scenario: Get by execution id - non-existing
    When I upload "1" artifacts to "package"
    When I get artifact by "wrong_execution_id"
    Then "NotFound" exception should be raised

  @packages.delete
  @testrail-C4523051
  Scenario: Use with package  - item
    When I upload "1" artifacts to "package"
    And I get artifact by "id"
    Then I receive an Artifact entity
    And Artifact received equals to the one uploaded

  @packages.delete
  @testrail-C4523051
  Scenario: Use with package name
    When I upload "1" artifacts to "package_name"
    And I get artifact by "package_name"
    Then I receive an Artifact entity
    And Artifact received equals to the one uploaded

  @packages.delete
  @services.delete
  @testrail-C4523051
  Scenario: Use with execution
    Given There is a service by the name of "artifacts-upload" with module name "default_module" saved to context "service"
    And I create a dataset with a random name
    And Item in path "0000000162.jpg" is uploaded to "Dataset"
    When I create an execution with "Item"
      |sync=False|inputs=Item|
    And I upload "1" artifacts to "execution"
    And I get artifact by "execution_id"
    Then I receive an Artifact entity
    And Artifact received equals to the one uploaded