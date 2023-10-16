Feature: Packages entity method testing

  Background: Initiate Platform Interface and create a project
    Given Platform Interface is initialized as dlp and Environment is set according to git branch
    And I create a project by the name of "test_package_module"
    And Directory "packages_get" is empty
    When I generate package by the name of "test-package" to "packages_get"

  @packages.delete
  @DAT-51155
  Scenario: Update PackageModule - Should be updated with expected values
    When I create PackageModule with params
      | name=package_module | entry_point=main.py | functions=[{'name':'run','inputs':'item'}] |
    And I update PackageModule function "1" input "1"
      | key  | value  |
      | name | item_1 |
    Then I verify PackageModule params
      | key                         | value  |
      | functions[0].inputs[0].name | item_1 |