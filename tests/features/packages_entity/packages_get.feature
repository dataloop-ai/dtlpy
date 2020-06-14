Feature: Packages entity method testing

    Background: Initiate Platform Interface and create a project
        Given Platform Interface is initialized as dlp and Environment is set according to git branch
        And There is a project by the name of "test_packages_get"
        And Directory "packages_get" is empty
        When I generate package by the name of "test_package" to "packages_entity"

    @packages.delete
    Scenario: To Json
        When I push "first" package
            |codebase_id=None|package_name=test-package|src_path=packages_get|inputs=None|outputs=None|
        When I get package by the name of "test-package"
        Then I get a package entity
        And Object "Package" to_json() equals to Platform json.