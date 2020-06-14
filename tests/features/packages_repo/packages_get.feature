Feature: Packages repository get service testing

    Background: Initiate Platform Interface and create a project
        Given Platform Interface is initialized as dlp and Environment is set according to git branch
        And There is a project by the name of "test_packages_get"
        And Directory "packages_get" is empty
        When I generate package by the name of "test-package" to "packages_get"

    @packages.delete
    Scenario: Get package by name
        When I push "first" package
            |codebase_id=None|package_name=test-package|src_path=packages_get|inputs=None|outputs=None|
        When I get package by the name of "test-package"
        Then I get a package entity
        And It is equal to package created

    @packages.delete
    Scenario: Get package by id
        When I push "first" package
            |codebase_id=None|package_name=test-package|src_path=packages_get|inputs=None|outputs=None|
        When I get package by id
        Then I get a package entity
        And It is equal to package created
