Feature: Annotation Entity Json to Object testing

    Background: Initiate Platform Interface
        Given Platform Interface is initialized as dlp and Environment is set to development
        And There is a project by the name of "Project_test_annotation_json_to_object"
        And I create a dataset by the name of "Dataset"

    Scenario: Image 
        Given Classes in file: "assets_split/ann_json_to_object/classes_new.json" are uploaded to test Dataset
        And Dataset ontology has attributes "attr1" and "attr2"
        And Item in path "assets_split/ann_json_to_object/0000000162.jpg" is uploaded to "Dataset"
        When Item is annotated with annotations in file: "assets_split/ann_json_to_object/annotations_new.json"
        Then Item annotations in host equal annotations in file "assets_split/ann_json_to_object/annotations_new.json"
        And Annotations to_json() equals to Platform json

    Scenario: Video
        Given Classes in file: "assets_split/ann_json_to_object/video_classes.json" are uploaded to test Dataset
        And Item in path "assets_split/ann_json_to_object/sample_video.mp4" is uploaded to "Dataset"
        When Item is annotated with annotations in file: "assets_split/ann_json_to_object/video_annotations.json"
        Then Item annotations in host equal annotations in file "assets_split/ann_json_to_object/video_annotations.json"
        And Annotations to_json() equals to Platform json
    
    Scenario: Finally
        Given Clean up
