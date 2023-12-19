Feature: Packages entity method testing

    Background: Initiate Platform Interface and create a project
        Given Platform Interface is initialized as dlp and Environment is set according to git branch
        And I create a project by the name of "test_packages_get"
        And Directory "packages_get" is empty
        When I generate package by the name of "test-package" to "packages_get"

    @packages.delete
    @testrail-C4523132
    @DAT-46557
    Scenario: To Json
        When I push "first" package
            |codebase_id=None|package_name=test-package|src_path=packages_get|inputs=None|outputs=None|
        When I get package by the name of "test-package"
        Then I get a package entity
        And Object "Package" to_json() equals to Platform json.

    @packages.delete
    @DAT-56141
    Scenario: test input description
        When I push "first" package
            |codebase_id=None|package_name=test-package|src_path=package_module|inputs=itemWithDescription|outputs=None|
        When I get package by the name of "test-package"
        Then I get a package entity
        And Object "Package" to_json() equals to Platform json.
        Then I verify PackageModule params
          | key                         | value  |
          | functions[0].inputs[0].description | item |
        When I update PackageModule function "1" input "1" use "package"
          | key  | value  |
          | description | item_1 |
        When I update package
        When i update the context module from package
        Then I verify PackageModule params
          | key                         | value  |
          | functions[0].inputs[0].description | item_1 |