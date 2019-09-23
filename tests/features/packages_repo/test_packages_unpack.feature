Feature: Packages repository Unpack method

    Background: Initiate Platform Interface and create a project
        Given Platform Interface is initialized as dlp and Environment is set to development
        And There is a project by the name of "packages_unpack"
        And I create a dataset with a random name

     Scenario: Unpack by name
         Given There is a Package directory with a python file in path "packages_assets/packages_unpack"
         And I pack directory by name "package_name1"
         When I unpack a package by the name of "package_name1" to "packages_assets/package_unpack"
         Then Unpacked package equal to package in "packages_assets/packages_unpack"

     Scenario: Unpack by id
         Given There is a Package directory with a python file in path "packages_assets/packages_unpack"
         And I pack directory by name "package_name2"
         When I unpack a package by the id of "package_name2" to "packages_assets/package_unpack"
         Then Unpacked package equal to package in "packages_assets/packages_unpack"

     Scenario: Unpack non-existing by name
         Given There is a Package directory with a python file in path "packages_assets/packages_unpack"
         And I pack directory by name "package_name3"
         When I try to unpack a package by the name of "some_name" to "packages_assets/package_unpack"
         Then "NotFound" exception should be raised

     Scenario: Unpack by non-existing id
         Given There is a Package directory with a python file in path "packages_assets/packages_unpack"
         And I pack directory by name "package_name4"
         When I try to unpack a package by the id of "some_id" to "packages_assets/package_unpack"
         Then "BadRequest" exception should be raised

     Scenario: Unpack - specific version
         Given There is a Package directory with a python file in path "packages_assets/packages_unpack"
         And I pack directory by name "package_name5"
         And I modify python file - (change version) in path "packages_assets/packages_unpack/some_code.py"
         And I pack directory by name "package_name5"
         When I unpack a package "package_name5" version "1" to "packages_assets/package_unpack"
         Then Unpacked package equal to package in "packages_assets/packages_unpack"

     Scenario: Unpack - latest version
         Given There is a Package directory with a python file in path "packages_assets/packages_unpack"
         And I pack directory by name "package_name6"
         And I modify python file - (change version) in path "packages_assets/packages_unpack/some_code.py"
         And I pack directory by name "package_name6"
         When I unpack a package "package_name6" version "latest" to "packages_assets/package_unpack"
         Then Unpacked package equal to package in "packages_assets/packages_unpack"

    Scenario: Unpack - all versions
        Given There is a Package directory with a python file in path "packages_assets/packages_unpack"
        And I pack directory by name "package_name7"
        And I modify python file - (change version) in path "packages_assets/packages_unpack/some_code.py"
        And I pack directory by name "package_name7"
        When I unpack a package "package_name7" version "all" to "packages_assets/package_unpack"
        Then I receive all versions in "packages_assets/package_unpack" and they are equal to versions in "packages_assets/packages_unpack/some_code.py"

    Scenario: Unpack - non-existing version
        Given There is a Package directory with a python file in path "packages_assets/packages_unpack"
        And I pack directory by name "package_name8"
        And I modify python file - (change version) in path "packages_assets/packages_unpack/some_code.py"
        And I pack directory by name "package_name8"
        When I try to unpack a package "package_name8" version "5" to "packages_assets/package_unpack"
        Then "NotFound" exception should be raised

