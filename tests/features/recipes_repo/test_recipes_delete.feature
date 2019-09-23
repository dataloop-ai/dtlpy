Feature: Recipes repository Delete function testing

    Background: Initiate Platform Interface and create a project
        Given Platform Interface is initialized as dlp and Environment is set to development
        And There is a project by the name of "recipes_delete"
        And I create a dataset with a random name

    Scenario: Delete recipe
        Given Dataset has Recipes
        When I delete recipe
        Then Dataset has no recipes

