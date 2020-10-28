Feature: Packages repository Context testing

    Background: Initiate Platform Interface and create a project
        Given Platform Interface is initialized as dlp and Environment is set according to git branch
        And I create projects by the name of "project1 project2"
        And I set Project to Project 1
        And Directory "packages_get" is empty
        When I generate package by the name of "test-package" to "packages_get"

    @packages.delete
    Scenario: Get Package from the project it belong to
        When I push "first" package
            |codebase_id=None|package_name=test-package|src_path=packages_get|inputs=None|outputs=None|
        When I get the package from project number 1
        Then Package project_id is equal to project 1 id
        And Package project.id is equal to project 1 id

    Scenario: Get Package from the project it is not belong to
        When I push "first" package
            |codebase_id=None|package_name=test-package|src_path=packages_get|inputs=None|outputs=None|
        When I get the package from project number 2
        Then Package project_id is equal to project 1 id
        And Package project.id is equal to project 1 id