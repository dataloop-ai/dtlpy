@bot.create
Feature: Services repository update with force=True service testing

     Background: Initiate Platform Interface and create a project
         Given Platform Interface is initialized as dlp and Environment is set according to git branch
         And I create a project by the name of "services_update"
         And I create a dataset with a random name
         And There is a package (pushed from "services/long_term") by the name of "services-update"
         And There is a service with max_attempts of "1" by the name of "services-update-force" with module name "default_module" saved to context "service"

     @services.delete
     @packages.delete
     @testrail-C4532327
     Scenario: Update service
        Given I execute service
        And Execution is running
        When I update service with force="True"
        Then Execution stopped immediately
