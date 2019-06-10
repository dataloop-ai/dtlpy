Feature: Packages repository Pack method

    Background: Initiate Platform Interface and create a project
        Given Platform Interface is initialized as dlp and Environment is set to development
        And There are no projects
        And There is a project by the name of "Project"
        And I create a dataset by the name of "Dataset"

    Scenario: Unpack a Package (init param: dataset, project, client_api)
        Given There is a Package directory with a python file in path "package"
        And I init packages with params project, dataset, client_api
        When I pack directory by name "package_name"
        Then I receive a Package object
        And Package in host equals package in path "package"

    Scenario: Pack a Package (init param: project, client_api)
        Given There is a Package directory with a python file in path "package"
        And I init packages with params project, client_api
        When I pack directory by name "package_name"
        Then I receive a Package object
        And Dataset by the name of "Binaries" was created
        And Package in host in dataset "Binaries" equals package in path "package"

    Scenario: Pack a Package - new version
        Given There is a Package directory with a python file in path "package"
        And I init packages with params project, dataset, client_api
        When I pack directory by name "package_name"
        And I modify python file - (change version) in path "package/some_code.py"
        And I pack directory by name "package_name"
        Then There should be "2" versions of the package "package_name" in host
    
    Scenario: Pack a Package - new version - nameless
        Given There is a Package directory with a python file in path "package"
        And I init packages with params project, dataset, client_api
        When I pack directory - nameless
        And I modify python file - (change version) in path "package/some_code.py"
        And I pack directory - nameless
        Then There should be "2" versions of the package "package" in host

    

