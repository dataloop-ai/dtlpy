Feature: Annotations collection testing

    Background: Initiate Platform Interface
        Given Platform Interface is initialized as dlp and Environment is set according to git branch
        And There is a project by the name of "Project_test_annotation_collection"
        And I create a dataset with a random name


    @testrail-C4523048
    Scenario: Annotation a text item
        When I upload a file in path "ann_text_object/tx.txt"
        Then Item exist in host
        When Item is annotated with annotations in file: "ann_text_object/text.json"
        Then Item annotations in host equal annotations in file "ann_text_object/text.json"
        And Object "Annotations" to_json() equals to Platform json.
