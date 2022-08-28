 Feature: Packages repository create slot testing

     Background: Initiate Platform Interface and create a project
         Given Platform Interface is initialized as dlp and Environment is set according to git branch
         And There is a project by the name of "test_packages_slot"
         And Directory "packages_create" is empty
         When I generate package by the name of "test-package" to "packages_create"

     @packages.delete
     @testrail-C4528974
     Scenario: Add UI slot to exist package
         When I push "first" package
             |codebase_id=None|package_name=test-package|src_path=packages_create|inputs=None|outputs=None|
         Then I receive package entity
         When I add UI slot to the package
         Then I validate slot is added to the package


     @packages.delete
     @testrail-C4528974
     Scenario: Add UI slot to exist package with all scopes
         When I push "first" package
             |codebase_id=None|package_name=test-package|src_path=packages_create|inputs=item,dataset,annotation,task|outputs=None|
         Then I receive package entity
         When I add UI slot to the package with all scopes
         Then I validate slot is added to the package
