Feature: Ontologies repository Update function testing

    Background: Initiate Platform Interface and create a project
        Given Platform Interface is initialized as dlp and Environment is set to development
        And There are no projects
        And There is a project by the name of "Project"
        And I create a dataset by the name of "Dataset"
        And Dataset has ontology

    Scenario: Update existig ontology labels
        When I update ontology with labels from file "labels.json"
        Then Dataset ontology in host equal ontology uploaded

    Scenario: Update existig ontology attributes
        When I update ontology attributes to "attr1", "attr2"
        Then Dataset ontology in host equal ontology uploaded

    Scenario: Update existig ontology metadata system
        When I update ontology system metadata
        Then Dataset ontology in host equal ontology uploaded