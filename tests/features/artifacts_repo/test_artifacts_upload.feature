@bot.create
Feature: Artifacts repository upload service testing

    Background: Initiate Platform Interface and create a project
        Given Platform Interface is initialized as dlp and Environment is set according to git branch
        And There is a project by the name of "test_artifacts_upload"
        And Directory "artifacts_upload" is empty
        When I generate package by the name of "test-package" to "artifacts_upload"

    @packages.delete
    Scenario: Use with package  - item
        Given Context "artifact_filepath" is "artifacts_repo/artifact_item.jpg"
        And Directory "artifacts_upload" is empty
        When I generate package by the name of "test_package" to "artifacts_upload"
        And I push "first" package
            | codebase_id=None | package_name=test-package | src_path=artifacts_upload | inputs=None | outputs=None |
        And I upload "1" artifacts to "package"
        Then I receive an artifact object

    @packages.delete
    Scenario: Use with package  - folder
        Given Context "artifact_filepath" is "artifacts_repo/artifact_folder"
        And Directory "artifacts_upload" is empty
        When I generate package by the name of "test_package" to "artifacts_upload"
        And I push "first" package
            | codebase_id=None | package_name=test-package | src_path=artifacts_upload | inputs=None | outputs=None |
        And I upload "1" artifacts to "package"
        Then I receive an artifact object

    @packages.delete
    Scenario: Use with package name
        Given Context "artifact_filepath" is "artifacts_repo/artifact_item.jpg"
        And Directory "artifacts_upload" is empty
        When I generate package by the name of "test_package" to "artifacts_upload"
        And I push "first" package
            | codebase_id=None | package_name=test-package | src_path=artifacts_upload | inputs=None | outputs=None |
        And I upload "1" artifacts to "package_name"
        Then I receive an artifact object

     @packages.delete
     @services.delete
     Scenario: Use with execution
         Given Context "artifact_filepath" is "artifacts_repo/artifact_item.jpg"
         And Directory "artifacts_upload" is empty
         When I generate package by the name of "test_package" to "artifacts_upload"
         And I push "first" package
             | codebase_id=None | package_name=test-package | src_path=artifacts_upload | inputs=None | outputs=None | modules=no_input |
         Given There is a service by the name of "artifacts-upload" with module name "default_module" saved to context "service"
         When I create an execution with "None"
             | sync=False |
         And I upload "1" artifacts to "execution"
         Then I receive an artifact object

     @packages.delete
     @services.delete
     Scenario: Use with execution id
         Given Context "artifact_filepath" is "artifacts_repo/artifact_item.jpg"
         And Directory "artifacts_upload" is empty
         When I generate package by the name of "test_package" to "artifacts_upload"
         And I push "first" package
             | codebase_id=None | package_name=test-package | src_path=artifacts_upload | inputs=None | outputs=None | modules=no_input |
         Given There is a service by the name of "artifacts-upload" with module name "default_module" saved to context "service"
         When I create an execution with "None"
             | sync=False |
         And I upload "1" artifacts to "execution_id"
         Then I receive an artifact object
