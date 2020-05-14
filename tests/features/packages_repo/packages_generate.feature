Feature: Packages repository generate service testing

  Background: Initiate Platform Interface and create a project
    Given Platform Interface is initialized as dlp and Environment is set according to git branch
    And There is a project by the name of "test_packages_generate"

  Scenario: Generate package - no given path - nameless
    Given Directory "packages_generate/to_generate" is empty
    And cwd is "packages_generate/to_generate"
    When I generate package by the name of "None" to "None"
    And cwd goes back to original
    Then package local files in "packages_generate/to_generate" equal package local files in "packages_generate/to_compare_nameless"

  Scenario: Generate package - no given path - by name
    Given Directory "packages_generate/to_generate" is empty
    And cwd is "packages_generate/to_generate"
    When I generate package by the name of "test-package" to "None"
    And cwd goes back to original
    Then Package local files in "packages_generate/to_generate" equal package local files in "packages_generate/to_compare_test_package"

  Scenario: Generate package by name
    Given Directory "packages_generate/to_generate" is empty
    When I generate package by the name of "test-package" to "packages_generate/to_generate"
    Then Package local files in "packages_generate/to_generate" equal package local files in "packages_generate/to_compare_test_package"

  Scenario: Generate package - nameless
    Given Directory "packages_generate/to_generate" is empty
    When I generate package by the name of "None" to "packages_generate/to_generate"
    Then Package local files in "packages_generate/to_generate" equal package local files in "packages_generate/to_compare_nameless"
