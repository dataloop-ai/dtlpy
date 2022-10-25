Feature: Recipe SDK

    Background: Initiate Platform Interface and create a project
        Given Platform Interface is initialized as dlp and Environment is set according to git branch
        And I create a project by the name of "my-project-recipe"
        And Create a Dataset "my-dataset-name"

    @testrail-C4523099
    Scenario: Recipe SDK Scenario
        When Get Recipe from List
        Then Get Recipe by ID
        And Recipe Clone
        And Delete Recipe
        And Recipe Switch

    @testrail-C4523099
    Scenario: Add Labels by Dataset
        When View Datasets Labels
        Then Add one Label "person"
        And Add Multiple Labels "person", "animal", "object"
        And Add a single label "person" with a specific color (34, 6, 231)
        And Add a single label "person" with a specific color (34, 6, 231) and attributes ["big", "small"]
        And Add a single label "car" with an image "assets_split/items_upload/0000000162.jpg" and attributes ["white","black"]
        And Add Labels using Label object
        And Add a Label with children and attributes
        And Add multiple Labels with children and attributes "My-Recipe-name"


    @testrail-C4523099
    Scenario: Add hierarchy labels with nested - Different options for hierarchy label creation.
        When Option A
        And Option B
        And Option C
        Then Create a Recipe From from a Label list "My-Recipe-name-1"
        And Update Label Features
        And Delete Labels by Dataset