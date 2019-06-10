Feature: Packages repository Unpack method

    Background: Initiate Platform Interface and create a project
        Given Platform Interface is initialized as dlp and Environment is set to development
        And There are no projects
        And There is a project by the name of "Project"
        And I create a dataset by the name of "Dataset"
        And There is a Package directory with a python file in path "package"
        And I init packages with params project, dataset, client_api
        And I pack directory by name "package_name"

    Scenario: Unpack by name
        When I unpack a package by the name of "package_name" to "package_unpack"
        Then Unpacked package equal to package in "package"

    Scenario: Unpack by id
        When I unpack a package by the id of "package_name" to "package_unpack"
        Then Unpacked package equal to package in "package"

    Scenario: Unpack non-existing by name
        When I try to unpack a package by the name of "some_name" to "package_unpack"
        Then "NotFound" exception should be raised

    Scenario: Unpack by non-existing id
        When I try to unpack a package by the id of "some_id" to "package_unpack"
        Then "InternalServerError" exception should be raised

    Scenario: Unpack - specific version
        Given I modify python file - (change version) in path "package/some_code.py"
        And I pack directory by name "package_name"
        When I unpack a package "package_name" version "1" to "package_unpack"
        Then Unpacked package equal to package in "package"

    Scenario: Unpack - latest version
        Given I modify python file - (change version) in path "package/some_code.py"
        And I pack directory by name "package_name"
        When I unpack a package "package_name" version "latest" to "package_unpack"
        Then Unpacked package equal to package in "package"

    Scenario: Unpack - all versions
        Given I modify python file - (change version) in path "package/some_code.py"
        And I pack directory by name "package_name"
        When I unpack a package "package_name" version "all" to "package_unpack"
        Then I receive all versions in "package_unpack" and they are equal to versions in "package/some_code.py"

    Scenario: Unpack - non-existing version
        Given I modify python file - (change version) in path "package/some_code.py"
        And I pack directory by name "package_name"
        When I try to unpack a package "package_name" version "5" to "package_unpack"
        Then "NotFound" exception should be raised
