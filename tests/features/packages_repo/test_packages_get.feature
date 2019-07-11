Feature: Packages repository Get method

    Background: Initiate Platform Interface and create a project
        Given Platform Interface is initialized as dlp and Environment is set to development
        And There is a project by the name of "packages_get"
        And I create a dataset by the name of "Dataset"

    Scenario: Get package by name
        Given There is a Package directory with a python file in path "packages_assets/packages_get"
        And I init packages with params project, dataset, client_api
        When I pack directory by name "package_name"
        And I modify python file - (change version) in path "packages_assets/packages_get/some_code.py"
        And I pack directory by name "package_name"
        When I get by name version "1" of package "package_name"
        Then I receive a Package object
        And Package received equal package packet

    Scenario: Get package by id
        Given There is a Package directory with a python file in path "packages_assets/packages_get"
        And I init packages with params project, dataset, client_api
        When I pack directory by name "package_name"
        And I modify python file - (change version) in path "packages_assets/packages_get/some_code.py"
        And I pack directory by name "package_name"
        When I get by id version "1" of package "package_name"
        Then I receive a Package object
        And Package received equal package packet

    Scenario: Get package by id - latest
        Given There is a Package directory with a python file in path "packages_assets/packages_get"
        And I init packages with params project, dataset, client_api
        When I pack directory by name "package_name"
        And I modify python file - (change version) in path "packages_assets/packages_get/some_code.py"
        And I pack directory by name "package_name"
        When I get by id version "latest" of package "package_name"
        Then I receive a Package object
        And Package received equal package packet

    Scenario: Get package by name - no version given
        Given There is a Package directory with a python file in path "packages_assets/packages_get"
        And I init packages with params project, dataset, client_api
        When I pack directory by name "package_name"
        And I modify python file - (change version) in path "packages_assets/packages_get/some_code.py"
        And I pack directory by name "package_name"
        When I get a package by name "package_name"
        Then I receive a Package object
        And Package received equal package packet

    Scenario: Get package by id - all
        Given There is a Package directory with a python file in path "packages_assets/packages_get"
        And I init packages with params project, dataset, client_api
        When I pack directory by name "package_name"
        And I modify python file - (change version) in path "packages_assets/packages_get/some_code.py"
        And I pack directory by name "package_name"
        When I get by name version "all" of package "package_name"
        Then I receive a list of Package objects
        And Package list have lenght of "2"

    Scenario: Finally
        Given Clean up