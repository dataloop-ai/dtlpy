Feature: Packages repository push service testing

    Background: Initiate Platform Interface and create a project
        Given Platform Interface is initialized as dlp and Environment is set according to git branch
        And I create a project by the name of "test_packages_push"
        And Directory "packages_push" is empty
        When I generate package by the name of "test-package" to "packages_push"

    @packages.delete
    @testrail-C4523139
    Scenario: Push local package - no params
        When I push "first" package
            |codebase_id=None|package_name=None|src_path=packages_push|inputs=None|outputs=None|
        Then I receive package entity
        And Package entity equals local package in "packages_generate/to_compare_test_package"
        When I modify python file - (change version) in path "packages_push/main.py"
        And I push "second" package
            |codebase_id=None|package_name=None|src_path=packages_push|inputs=None|outputs=None|
        Then I receive another package entity
        And 1st package and 2nd package only differ in code base id
