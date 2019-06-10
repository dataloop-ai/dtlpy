Feature: Project Entity repo functions

    Background: Initiate Platform Interface
        Given Platform Interface is initialized as dlp and Environment is set to development
        And There are no projects
        And There is a project by the name of "Project"

    # Scenario: List Datasets
    #     Given I create a dataset by the name of "Dataset1"
    #     And I create a dataset by the name of "Dataset2"
    #     When I list project entity datasets
    #     Then I receive a datasets list of "2" dataset

    # Scenario: Get an existing dataset by name
    #     Given There are no datasets
    #     And I create a dataset by the name of "Dataset"
    #     When I get project entity dataset by the name of "Dataset"
    #     Then I get a dataset by the name of "Dataset"
    #     And The dataset I got is equal to the one created

    # Scenario: Create a dataset
    #     Given There are no datasets
    #     When I create by project entity a dataset by the name of "Dataset"
    #     Then Dataset object by the name of "Dataset" should be exist
    #     And Dataset by the name of "Dataset" should exist in host

    Scenario: Delete project
        When I delete a project entity
        Then There are no projects

    Scenario: Update projects name
        When I change project name to "new_project_name"
        Then Project in host has name "new_project_name"

    # Scenario: Pack a Package
    #     Given There is a Package directory with a python file in path "package"
    #     When I use project entity to pack directory by name "package_name"
    #     Then I receive a Package object
    #     And Dataset by the name of "Binaries" was created
    #     And ent - Package in host in dataset "Binaries" equals package in path "package"