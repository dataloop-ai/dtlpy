Feature: Ontology Labels with icon

    Background: Initiate Platform Interface
        Given Platform Interface is initialized as dlp and Environment is set according to git branch
        And There is a project by the name of "ontology_bamba_feature"
        And I create a dataset with a random name
        And Dataset has ontology

    @testrail-C4532189
    Scenario: Add images to labels from different folders
        When I add label "1" to ontology with "labels/1/bamba-icon.jpg"
        When I add label "2" to ontology with "labels/2/bamba-icon.jpg"
        Then I validate dataset labels images are different