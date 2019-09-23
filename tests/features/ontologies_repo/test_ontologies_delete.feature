Feature: Ontologies repository Delete function testing

    Background: Initiate Platform Interface and create a project
        Given Platform Interface is initialized as dlp and Environment is set to development
        And There is a project by the name of "ontologies_delete"
        And I create a dataset with a random name
        And Dataset has ontology

    Scenario: Delete existing ontology by id
        When I delete ontology by id
        Then Ontology does not exist in dataset

    Scenario: Delete non-existing ontology by id
        When I try to delete ontology by "some_id"
        Then "BadRequest" exception should be raised

