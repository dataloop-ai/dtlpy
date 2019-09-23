Feature: Recipes repository Update function testing

    Background: Initiate Platform Interface and create a project
        Given Platform Interface is initialized as dlp and Environment is set to development
        And There is a project by the name of "recipes_edit"
        And I create a dataset with a random name

    Scenario: Update recipe
        When I update recipe
        Then Recipe in host equals recipe eddited

