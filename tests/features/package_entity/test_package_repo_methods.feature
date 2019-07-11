Feature: Package Entity repo functions

    Background: Initiate Platform Interface
        Given Platform Interface is initialized as dlp and Environment is set to development
        And There is a project by the name of "package_repo_methods"
        And I create a dataset by the name of "Dataset"
        And There is a Package directory with a python file in path "packages_assets/package_entity"
        And I pack from project.packages directory by name "package_name"

    Scenario: Unpack by name
        When I unpack a package entity by the name of "package_name" to "packages_assets/package_entity_unpack"
        Then Unpacked package equal to package in "packages_assets/package_entity"

    Scenario: List all versions when 2 exist
        When I modify python file - (change version) in path "packages_assets/package_entity/some_code.py"
        Given I pack from project.packages directory by name "package_name"
        When I list versions of package entity "package_name"
        Then I receive a list of "2" versions

    Scenario: Finally
        Given Clean up