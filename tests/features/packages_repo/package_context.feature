 Feature: Packages repository context service testing

     Background: Initiate Platform Interface and create a project
         Given Platform Interface is initialized as dlp and Environment is set according to git branch
         And There is a project by the name of "test_packages_context"

     @packages.delete
     @testrail-C4523134
     Scenario: Create package
         When I push "first" package
             |codebase_id=None|package_name=test-package|src_path=packages_context|inputs=None|outputs=None|
         Then I receive package entity
         And Package entity equals local package in "packages_context"
