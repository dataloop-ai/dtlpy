Feature: Annotation Entity Json to Object testing

    Background: Initiate Platform Interface
        Given Platform Interface is initialized as dlp and Environment is set according to git branch
        And I create a project by the name of "Project_test_annotation_json_to_object"
        And I create a dataset with a random name

    @testrail-C4523043
    @DAT-46444
    Scenario: Image 
        Given Classes in file: "assets_split/ann_json_to_object/classes_new.json" are uploaded to test Dataset
        And Item in path "assets_split/ann_json_to_object/0000000162.jpg" is uploaded to "Dataset"
        When I add "free_text" attribute to ontology
            | key=1 | title=attr1 | scope=all |
        When I add "free_text" attribute to ontology
            | key=2 | title=attr2 | scope=all |
        When Item is annotated with annotations in file: "assets_split/ann_json_to_object/annotations_new.json"
        Then Item annotations in host equal annotations in file "assets_split/ann_json_to_object/annotations_new.json"
        And Object "Annotations" to_json() equals to Platform json.

    @testrail-C4523043
    @DAT-46444
    Scenario: Video
        Given Classes in file: "assets_split/ann_json_to_object/video_classes.json" are uploaded to test Dataset
        And Item in path "assets_split/ann_json_to_object/sample_video.mp4" is uploaded to "Dataset"
        When Item is annotated with annotations in file: "assets_split/ann_json_to_object/video_annotations.json"
        Then Item annotations in host equal annotations in file "assets_split/ann_json_to_object/video_annotations.json"
        And Object "Annotations" to_json() equals to Platform json.
