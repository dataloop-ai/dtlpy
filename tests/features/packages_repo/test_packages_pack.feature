Feature: Packages repository Pack method

    Background: Initiate Platform Interface and create a project
        Given Platform Interface is initialized as dlp and Environment is set to development
        And There is a project by the name of "packages_pack"
        And I create a dataset with a random name

    Scenario: Unpack a Package (init param: dataset, project, client_api)
        Given There is a Package directory with a python file in path "packages_assets/packages_pack"
        And I init packages with params project, dataset, client_api
        When I pack directory by name "package_name"
        Then I receive a Package object
        And Package in host when downloaded to "packages_pack_unpack" equals package in path "packages_assets/packages_pack"

    Scenario: Pack a Package (init param: project, client_api)
        Given There is a Package directory with a python file in path "packages_assets/packages_pack"
        And I init packages with params project, client_api
        When I pack directory by name "package_name"
        Then I receive a Package object
        And Dataset by the name of "Binaries" was created
        And Package in host in dataset "Binaries", when downloaded to "packages_pack_unpack" equals package in path "packages_assets/packages_pack"

    Scenario: Pack a Package - new version
        Given There is a Package directory with a python file in path "packages_assets/packages_pack"
        And I init packages with params project, dataset, client_api
        When I pack directory by name "package_name"
        And I modify python file - (change version) in path "packages_assets/packages_pack/some_code.py"
        And I pack directory by name "package_name"
        Then There should be "2" versions of the package "package_name" in host
    
    Scenario: Pack a Package - new version - nameless
        Given There is a Package directory with a python file in path "packages_assets/packages_pack"
        And I init packages with params project, dataset, client_api
        When I pack directory - nameless
        And I modify python file - (change version) in path "packages_assets/packages_pack/some_code.py"
        And I pack directory - nameless
        Then There should be "2" versions of the package "package" in host

    Scenario: Finally
        Given Clean up