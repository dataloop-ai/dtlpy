Feature: Ontologies repository get service testing

    Background: Initiate Platform Interface and create a project
        Given Platform Interface is initialized as dlp and Environment is set according to git branch
        And I create a project by the name of "ontologies_get"
        And I create a dataset with a random name

    @testrail-C4523130
    Scenario: Get an existing ontology by id
        Given Dataset has ontology
        When I get a ontology by id
        Then I get an Ontology object

    @testrail-C4523130
    Scenario: Get non-existing Ontology by id
        Given Dataset has ontology
        When I try to get Ontology by "some_id"
        Then "BadRequest" exception should be raised

