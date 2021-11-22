Feature: Recipes repository create service testing

    Background: Initiate Platform Interface and create a project
        Given Platform Interface is initialized as dlp and Environment is set according to git branch
        And There is a project by the name of "Project_test_recipes_create"
        And I create a dataset with a random name

    @testrail-C4523152
    Scenario: Create new recipe - plain
        When I create a new plain recipe
        And I update dataset recipe to the new recipe
        Then Dataset recipe in host equals the one created

    @testrail-C4523152
    Scenario: Create new recipe - labels and attributes
        When I create a new recipe with param labels from "labels.json" and attributes: "attr1", "attr2"
        And I update dataset recipe to the new recipe
        Then Dataset recipe in host equals the one created
        And Dataset ontology in host has labels from "labels.json" and attributes: "attr1", "attr2"

    @testrail-C4523152
    Scenario: Create new recipe - with existing ontology id
        When I create a new plain recipe with existing ontology id
        And I update dataset recipe to the new recipe
        Then Dataset recipe in host equals the one created
