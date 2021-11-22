 Feature: Checkouts

   Background: Background
     Given Platform Interface is initialized as dlp and Environment is set according to git branch
     And There is a project by the name of "items_download_batch"
     And Get feature entities
       |dataset|codebase|package|service|

   @packages.delete
   @services.delete
   @testrail-C4523066
   Scenario: Feature entities
     Given Feature: I create a dataset by the name of "Dataset"
     When I checkout
       |project|
     Given Feature: There is a package and service
     And Done setting

   @testrail-C4523066
   Scenario: Projects
     When I checkout
       |project|
     Then I am checked out
       |project|

   @testrail-C4523066
   Scenario: Dataset
     When I checkout
       |dataset|
     Then I am checked out
       |dataset|

   @testrail-C4523066
   Scenario: Package
     When I checkout
       |package|
     Then I am checked out
       |package|

    @testrail-C4523066
    Scenario: Service
     When I checkout
       |service|
     Then I am checked out
       |service|
