Feature: Ontology Entity attributes testing

    Background: Initiate Platform Interface
        Given Platform Interface is initialized as dlp and Environment is set according to git branch
        And There is a project by the name of "ontology_attributes"
        And I create a dataset with a random name
        And Dataset has ontology
        And Classes in file: "classes_new.json" are uploaded to test Dataset


    @testrail-C4529142
    Scenario: Add attributes to ontology
        When I add "checkbox" attribute to ontology
            |key=1 | title=test1 | values=['a','b','c'] |
        Then I validate attribute "checkbox" added to ontology
        When I add "radio_button" attribute to ontology
            |key=2 | title=test2 | values=['a','b','c'] | scope=all |
        Then I validate attribute "radio_button" added to ontology
        When I add "slider" attribute to ontology
            |key=3 | title=test3 | scope=all | attribute_range=0,10,1 |
        Then I validate attribute "slider" added to ontology
        When I add "yes_no" attribute to ontology
            |key=4 | title=test4 | scope=all |
        Then I validate attribute "yes_no" added to ontology
        When I add "free_text" attribute to ontology
            |key=5 | title=test5 | scope=all |
        Then I validate attribute "free_text" added to ontology


    @testrail-C4529142
    Scenario: Delete ontology attributes
        When I add "checkbox" attribute to ontology
            |key=1 | title=test1 | values=['a','b','c'] | scope=all |
        Then I delete attributes with key "1" in ontology
        When I add "checkbox" attribute to ontology
            |key=1 | title=test1 | values=['a','b','c'] | scope=all |
        And I add "slider" attribute to ontology
            |key=3 | title=test3 | scope=all | attribute_range=0,10,1 |
        And I add "free_text" attribute to ontology
            |key=5 | title=test5 | scope=all |
        Then I delete all attributes in ontology


    @testrail-C4529142
    Scenario: Attributes Edge cases
        # I Add attribute with all params
        When I add "checkbox" attribute to ontology
            |key=1 | title=test1 | values=['a','b','c'] | scope=['Person','Wheel'] | optional=False |
        Then I validate attribute "checkbox" added to ontology
        # I Add attribute with int value
        When I add "checkbox" attribute to ontology
            |key=1 | title=test1 | values=[1] |
        Then I receive error with status code "400"
