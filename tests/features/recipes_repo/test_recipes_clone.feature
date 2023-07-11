Feature: Recipes repository clone service testing

    Background: Initiate Platform Interface and create a project
        Given Platform Interface is initialized as dlp and Environment is set according to git branch
        And I create projects by the name of "project1 project2"
        And I create datasets by the name of "dataset1 dataset2"
        And I set Dataset to Dataset 1
        And I set dataset recipe and ontology to context
        When I add new label "111" to dataset 1
        And I add new label "222" to dataset 1


    @testrail-C4523151
    @DAT-46599
    Scenario: Clone recipe and Ontology
        When I clone recipe from  dataset 1 to dataset 2 with ontology
        And I add new label "333" to dataset 2
        Then I verify that Dataset 1 has 2 labels
        And I verify that Dataset 2 has 3 labels


    @testrail-C4523151
    @DAT-46599
    Scenario: Clone recipe without Ontology
        When I clone recipe from  dataset 1 to dataset 2 without ontology
        And I add new label "333" to dataset 2
        Then I verify that Dataset 1 has 3 labels
        And I verify that Dataset 2 has 3 labels
