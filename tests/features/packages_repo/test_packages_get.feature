Feature: Packages repository Get method

    Background: Initiate Platform Interface and create a project
        Given Platform Interface is initialized as dlp and Environment is set to development
        And There are no projects
        And There is a project by the name of "Project"
        And I create a dataset by the name of "Dataset"
        And There is a Package directory with a python file in path "package"
        And I init packages with params project, dataset, client_api
        When I pack directory by name "package_name"
        And I modify python file - (change version) in path "package/some_code.py"
        And I pack directory by name "package_name"

    Scenario: Get package by name
        When I get by name version "1" of package "package_name"
        Then I receive a Package object
        And Package received equal package packet

    Scenario: Get package by id
        When I get by id version "1" of package "package_name"
        Then I receive a Package object
        And Package received equal package packet

    Scenario: Get package by id - latest
        When I get by id version "latest" of package "package_name"
        Then I receive a Package object
        And Package received equal package packet

    Scenario: Get package by name - no version given
        When I get a package by name "package_name"
        Then I receive a Package object
        And Package received equal package packet

    Scenario: Get package by id - all
        When I get by name version "all" of package "package_name"
        Then I receive a list of Package objects
        And Package list have lenght of "2"