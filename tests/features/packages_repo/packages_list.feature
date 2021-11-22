Feature: Packages repository list service testing

    Background: Initiate Platform Interface and create a project
        Given Platform Interface is initialized as dlp and Environment is set according to git branch
        And There is a project by the name of "test_packages_list"
        And Directory "packages_list" is empty
        When I generate package by the name of "test-package" to "packages_list"

    @testrail-C4523137
    Scenario: list packages when 0 exist
        When I list all project packages
        Then I receive a list of "0" packages

    @packages.delete
    @testrail-C4523137
    Scenario: list packages when 1 exist
        When I push "first" package
            |codebase_id=None|package_name=None|src_path=packages_list|inputs=None|outputs=None|
        Then I receive package entity
        And Package entity equals local package in "packages_generate/to_compare_test_package"
        When I list all project packages
        Then I receive a list of "1" packages

