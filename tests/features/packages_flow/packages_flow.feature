@bot.create
Feature: Packages Flow

    Background: Initiate Platform Interface and create a project
        Given Platform Interface is initialized as dlp and Environment is set according to git branch
        And I create a project by the name of "test_packages_flow"
        And I create a dataset with a random name
        And Directory "package_flow/package_directory" is empty

    @services.delete
    @packages.delete
    @testrail-C4523133
    @DAT-46558
    Scenario: Standard Flow
        When I generate package by the name of "None" to "package_flow/package_directory"
        And I upload a file in path "package_flow/package_assets/picture1.jpg"
        And I copy all relevant files from "package_flow/package_assets" to "package_flow/package_directory"
        And I test local package in "package_flow/package_directory"
        And I push and deploy package in "package_flow/package_directory"
        And I upload item in "package_flow/package_assets/picture2.jpg" to dataset
        Then Item "1" annotations equal annotations in "package_flow/package_assets/annotations1.json"
        And Item "2" annotations equal annotations in "package_flow/package_assets/annotations2.json"
