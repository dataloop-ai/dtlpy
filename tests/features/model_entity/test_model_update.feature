Feature: Model entity update testing

     Background: Initiate Platform Interface and create a project
         Given Platform Interface is initialized as dlp and Environment is set according to git branch
         And There is a project by the name of "model.update"

     @testrail-C4523126
     Scenario: Update a model with tags
         Given There are no models
         And I create a model with a random name
         When I change model tags
         Then Model tags was changed


