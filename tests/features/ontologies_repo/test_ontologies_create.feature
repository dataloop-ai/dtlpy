Feature: Ontologies repository create service testing

    Background: Initiate Platform Interface and create a project
        Given Platform Interface is initialized as dlp and Environment is set according to git branch
        And I create a project by the name of "ontologies_create"
        And I create a dataset with a random name

    @testrail-C4523127
    Scenario: Create ontology
        When I create a new ontology with labels from file "labels.json"
        And I update dataset ontology to the one created
        Then Dataset ontology in host equal ontology uploaded

    @testrail-C4523127
    Scenario: Create ontology - no project id
        When I create a new ontology with no projectIds, with labels from file "labels.json"
        And I update dataset ontology to the one created
        Then Dataset ontology in host equal ontology uploaded

    @testrail-C4523127
    Scenario: Create ontology with attributes
        When I create a new ontology with labels from file "labels.json" and attributes "['attr1', 'attr2']"
        And I update dataset ontology to the one created
        Then Dataset ontology in host equal ontology uploaded

    # not working properly
    # Scenario: Create ontology - other project id
    #     Given There is another project by the name of "other_project"
    #     When I create a new ontology with labels and project id of "other_project" from file "labels.json"
    #     And I try to update dataset ontology to the one created
    #     Then "Forbidden" exception should be raised

    @testrail-C4523127
    Scenario: Create ontology - wrong project id
        When I try create a new ontology with labels and "some_project_id" from file "labels.json"
        Then "Forbidden" exception should be raised


