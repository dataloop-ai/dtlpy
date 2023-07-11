Feature: Packages repository delete testing

  Background: Initiate Platform Interface and create a project
    Given Platform Interface is initialized as dlp and Environment is set according to git branch
    And I create a project by the name of "test_packages_delete"
    And Directory "packages_create" is empty
    When I generate package by the name of "test-package" to "packages_create"

  @testrail-C4532690
  @DAT-46560
  Scenario: Create package
    When I push "first" package
      | codebase_id=None | package_name=test-package | src_path=packages_create | inputs=None | outputs=None |
    Then I receive package entity
    And I delete package

