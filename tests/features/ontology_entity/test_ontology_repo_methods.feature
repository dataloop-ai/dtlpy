Feature: Ontology Entity repo services

    Background: Initiate Platform Interface
        Given Platform Interface is initialized as dlp and Environment is set according to git branch
        And There is a project by the name of "ontology_repo_methods"
        And I create a dataset with a random name
        And Dataset has ontology

    @testrail-C4523131
    Scenario: Add label to ontology
        When I add label to ontology
        And I update ontology entity
        Then Ontology in host has label

    @testrail-C4523131
    Scenario: Add labels to ontology and to_root() testing
        When I update ontology entity with labels from file "labels.json"
        Then Dataset ontology in host has labels uploaded from "labels.json"

    @testrail-C4523131
    Scenario: Delete item
        When I delete ontology entity
        Then Ontology does not exist in dataset

    @testrail-C4523131
    Scenario: Update existing ontology labels
        When I update ontology entity with labels from file "labels.json"
        Then Dataset ontology in host equal ontology uploaded

    @testrail-C4523131
    Scenario: Update existing ontology metadata system
        When I update ontology entity system metadata
        Then Dataset ontology in host equal ontology uploaded


