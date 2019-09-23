Feature: Packages repository Get method

    Background: Initiate Platform Interface and create a project
        Given Platform Interface is initialized as dlp and Environment is set to development
        And There is a project by the name of "packages_get"
        And I create a dataset with a random name

    Scenario: Get package by name
        Given There is a Package directory with a python file in path "packages_assets/packages_get"
        When I pack directory by name "package_name1"
        And I modify python file - (change version) in path "packages_assets/packages_get/some_code.py"
        And I pack directory by name "package_name1"
        When I get by name version "1" of package "package_name1"
        Then I receive a Package object
        And Package received equal package packet

    Scenario: Get package by id
        Given There is a Package directory with a python file in path "packages_assets/packages_get"
        When I pack directory by name "package_name2"
        And I modify python file - (change version) in path "packages_assets/packages_get/some_code.py"
        And I pack directory by name "package_name2"
        When I get by id version "1" of package "package_name2"
        Then I receive a Package object
        And Package received equal package packet

    Scenario: Get package by id - latest
        Given There is a Package directory with a python file in path "packages_assets/packages_get"
        When I pack directory by name "package_name3"
        And I modify python file - (change version) in path "packages_assets/packages_get/some_code.py"
        And I pack directory by name "package_name3"
        When I get by id version "latest" of package "package_name3"
        Then I receive a Package object
        And Package received equal package packet

    Scenario: Get package by name - no version given
        Given There is a Package directory with a python file in path "packages_assets/packages_get"
        When I pack directory by name "package_name4"
        And I modify python file - (change version) in path "packages_assets/packages_get/some_code.py"
        And I pack directory by name "package_name4"
        When I get a package by name "package_name4"
        Then I receive a Package object
        And Package received equal package packet

    Scenario: Get package by id - all
        Given There is a Package directory with a python file in path "packages_assets/packages_get"
        When I pack directory by name "package_name5"
        And I modify python file - (change version) in path "packages_assets/packages_get/some_code.py"
        And I pack directory by name "package_name5"
        When I get by name version "all" of package "package_name5"
        Then I receive a list of Package objects
        And Package list have lenght of "2"

