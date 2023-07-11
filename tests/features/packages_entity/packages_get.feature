Feature: Packages entity method testing

    Background: Initiate Platform Interface and create a project
        Given Platform Interface is initialized as dlp and Environment is set according to git branch
        And I create a project by the name of "test_packages_get"
        And Directory "packages_get" is empty
        When I generate package by the name of "test-package" to "packages_get"

    @packages.delete
    @testrail-C4523132
    @DAT-46557
    Scenario: To Json
        When I push "first" package
            |codebase_id=None|package_name=test-package|src_path=packages_get|inputs=None|outputs=None|
        When I get package by the name of "test-package"
        Then I get a package entity
        And Object "Package" to_json() equals to Platform json.
