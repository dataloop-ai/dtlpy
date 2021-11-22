Feature: Recipes entity methods testing

    Background: Initiate Platform Interface and create a project
        Given Platform Interface is initialized as dlp and Environment is set according to git branch
        And There is a project by the name of "recipes_entity_methods"
        And I create a dataset with a random name

    @testrail-C4523155
    Scenario: To Json
        Given Dataset has Recipes
        Then Object "Recipe" to_json() equals to Platform json.