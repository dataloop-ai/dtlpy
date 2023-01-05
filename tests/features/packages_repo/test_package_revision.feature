@bot.create
Feature: Packages revision testing

     Background: Initiate Platform Interface and create a project
         Given Platform Interface is initialized as dlp and Environment is set according to git branch
         And I create a project by the name of "test_package_revision"
         And Directory "packages_create" is empty
         When I generate package by the name of "test-package" to "packages_create"

     @packages.delete
     @testrail-C4532574
     Scenario: Update package revision Should update the package version
         When I push "first" package
             |codebase_id=None|package_name=test-package|src_path=packages_create|inputs=None|outputs=None|
         Then I receive package entity
         And I expect package version to be "1.0.0" and revision list size "1"
         When I update package
         Then I expect package version to be "1.0.1" and revision list size "2"
         When I update package
         Then I expect package version to be "1.0.2" and revision list size "3"


     @services.delete
     @packages.delete
     @testrail-C4532574
     Scenario: Update package revision and install specific service version
         When I push "first" package
             |codebase_id=None|package_name=test-package|src_path=packages_create|inputs=None|outputs=None|
         Then I receive package entity
         When I update package
         And I update package
         Then I expect package version to be "1.0.2" and revision list size "3"
         When I create a service
            |service_name=services-get|package=services-get|revision=1.0.1|config=None|runtime=None|
         Then I validate service version is "1.0.1"


    @pipelines.delete
    @testrail-C4532574
    Scenario: Update pipeline and update code node - package revision should updated
      Given I create a dataset with a random name
      When I create a new plain recipe
      And I update dataset recipe to the new recipe
      And I create a pipeline with code node
      Then I wait "4"
      And I pause pipeline in context
      And I wait "4"
      When I update pipeline code node
      Then I install pipeline in context
      And I wait "4"
      And I validate pipeline code-node service is with the correct version "1.0.1"


    @pipelines.delete
    @testrail-C4532574
    Scenario: Update pipeline with code node not update the package revision
      Given I create a dataset with a random name
      When I create a new plain recipe
      And I update dataset recipe to the new recipe
      And I create a pipeline with code and task node
      Then I wait "4"
      And I pause pipeline in context
      And I wait "4"
      And I install pipeline in context
      And I validate pipeline code-node service is with the correct version "1.0.0"
