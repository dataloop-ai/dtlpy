Feature: Ontology Entity repo functions

    Background: Initiate Platform Interface
        Given Platform Interface is initialized as dlp and Environment is set to development
        And There is a project by the name of "ontology_repo_methods"
        And I create a dataset by the name of "Dataset"
        And Dataset has ontology

    Scenario: Add label to ontology
        When I add label to ontology
        And I update ontology entity
        Then Ontology in host has label

    Scenario: Add labels to ontology and to_root() testing
        When I update ontology entity with labels from file "labels.json"
        Then Dataset ontology in host has labels uploaded from "labels.json"

    Scenario: Delete item
        When I delete ontology entity
        Then Ontology does not exist in dataset

    Scenario: Update existig ontology labels
        When I update ontology entity with labels from file "labels.json"
        Then Dataset ontology in host equal ontology uploaded

    Scenario: Update existig ontology metadata system
        When I update ontology entity system metadata
        Then Dataset ontology in host equal ontology uploaded

    Scenario: Finally
        Given Clean up "ontology_repo_methods"
