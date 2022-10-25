 Feature: Packages repository create service testing

     Background: Initiate Platform Interface and create a project
         Given Platform Interface is initialized as dlp and Environment is set according to git branch
         And I create a project by the name of "test_packages_create"

     @testrail-C4523138
     Scenario: Create package with illegal name
         When I try to push package
             |codebase_id=None|package_name=illegal_name|src_path=packages_create|inputs=None|outputs=None|
         Then "BadRequest" exception should be raised
         And Name is invalid

     @testrail-C4523138
     Scenario: Validate names
         When I validate name "1package"
         Then Name is invalid
         When I validate name "my_package"
         Then Name is invalid
         When I validate name "-package"
         Then Name is invalid
         When I validate name "package-"
         Then Name is invalid
         When I validate name "Package"
         Then Name is invalid
         When I validate name "packageabcderthjgkldkfjghrnfhdbchfnvjghgj"
         Then Name is invalid
         When I validate name "package"
         Then Name is valid
         When I validate name "my-package"
         Then Name is valid
         When I validate name "package-number-1"
         Then Name is valid