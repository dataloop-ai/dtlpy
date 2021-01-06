Feature: Add Labels include nested Labels

    Background: Initiate Platform Interface
        Given Platform Interface is initialized as dlp and Environment is set according to git branch
        And There is a project by the name of "Project_test_annotation_add"
        And I create a dataset with a random name
        And There is no label with the same label I plan to add

    Scenario: Add single root Label with all parameters
        When I add new single label with all parameters
        Then Label has been added

    Scenario: Add single root Label with all parameters with no update_ontology parameter
        When I add new single label with all parameters with no update_ontology parameter
        Then Label has been added

    Scenario: Add single root Label with same label name twice
        When I add single root Label
        Then I add single root Label

    Scenario: Add single root Label with Label name only
        When I add single root Label with Label name only
        Then Label has been added

    Scenario: Add single nested root Label with all parameters
        When I add single nested root Label with all parameters
        Then Label has been added

    Scenario: Add single nested Label with Label name only
        When I add single nested Label with Label name only
        Then Label has been added

    Scenario: Add single nested label using ontology.add_label when update_ontology is true
        When I add single nested label using ontology.add_label when update_ontology is true
        Then Label has been added

    Scenario: Add single nested label using ontology.add_label when update_ontology is false
        Then I add single nested label using ontology.add_label when update_ontology is false

    Scenario: Add single not nested label using ontology.add_label when update_ontology is false
        When I add single not nested label using ontology.add_label when update_ontology is false
        Then Label has been added

    Scenario: Add labels of string type
        When I add labels of string type
        Then Label has been added

    Scenario: Add labels of string type using ontology.add_labels when update_ontology is false
        When I add labels of string type using ontology.add_labels when update_ontology is false
        Then Label has been added

    Scenario: Add and Update many labels
        When I add many labels
        Then Label has been added
        And  I update many labels
        And Label has been added
        And  I upsert many labels
        And Label has been added

    Scenario: Add many nested labels
        When I add many nested labels
        Then Label has been added
