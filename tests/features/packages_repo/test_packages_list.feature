Feature: Packages repository List method

    Background: Initiate Platform Interface and create a project
        Given Platform Interface is initialized as dlp and Environment is set to development
        And There is a project by the name of "packages_list"
        And I create a dataset by the name of "Dataset"

    Scenario: List all packages when 2 exist
        Given There is a Package directory with a python file in path "packages_assets/packages_list"
        And I init packages with params project, dataset, client_api
        When I pack directory by name "package1_name"
        And I pack directory by name "package2_name"
        When I list all packages
        Then I receive a list of "2" packages

    Scenario: List all versions when 1 exist
        Given There is a Package directory with a python file in path "packages_assets/packages_list"
        And I init packages with params project, dataset, client_api
        When I pack directory by name "package_name"
        When I list all packages
        Then I receive a list of "1" packages

    Scenario: List all versions when 0 exist
        Given I init packages with params project, dataset, client_api
        When I list all packages
        Then I receive a list of "0" packages

    Scenario: Finally
        Given Clean up