Feature: Packages repository List Version method

    Background: Initiate Platform Interface and create a project
        Given Platform Interface is initialized as dlp and Environment is set to development
        And There is a project by the name of "packages_list_versions"
        And I create a dataset by the name of "Dataset"

    Scenario: List all versions when 2 exist
        Given There is a Package directory with a python file in path "packages_assets/packages_list_versions"
        And I init packages with params project, dataset, client_api
        When I pack directory by name "package_name"
        And I modify python file - (change version) in path "packages_assets/packages_list_versions/some_code.py"
        And I pack directory by name "package_name"
        When I list versions of "package_name"
        Then I receive a list of "2" versions

    Scenario: List all versions when 1 exist
        Given There is a Package directory with a python file in path "packages_assets/packages_list_versions"
        And I init packages with params project, dataset, client_api
        When I pack directory by name "package_name"
        When I list versions of "package_name"
        Then I receive a list of "1" versions

    Scenario: List all versions when 0 exist
        Given I init packages with params project, dataset, client_api
        When I list versions of "package_name"
        Then I receive a list of "0" versions

    Scenario: Finally
        Given Clean up