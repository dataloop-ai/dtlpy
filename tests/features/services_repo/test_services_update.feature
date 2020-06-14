@bot.create
Feature: Services repository update service testing

     Background: Initiate Platform Interface and create a project
         Given Platform Interface is initialized as dlp and Environment is set according to git branch
         And There is a project by the name of "services_update"
         And I create a dataset with a random name
         And There is a package (pushed from "services/item") by the name of "services-update"
         And There is a service by the name of "services-update" with module name "default_module" saved to context "service"

     @services.delete
     @packages.delete
     Scenario: Update service
         When I change service "concurrency" to "17"
         And I update service
         Then Service received equals service changed except for "runtime.concurrency"
