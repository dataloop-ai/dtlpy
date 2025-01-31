Feature: Annotations collection testing

    Background: Initiate Platform Interface
        Given Platform Interface is initialized as dlp and Environment is set according to git branch
        And I create a project by the name of "Project_test_annotation_collection"
        And I create a dataset with a random name
        When I add "free_text" attribute to ontology
              | key=1 | title=attr1 | scope=all |
        When I add "free_text" attribute to ontology
            | key=2 | title=attr2 | scope=all |

    @testrail-C4523040
    @DAT-46436
   Scenario: Update - image
       Given Classes in file: "classes_new.json" are uploaded to test Dataset
       And Item in path "assets_split/annotation_collection/0000000162.jpg" is uploaded to "Dataset"
       And Item is annotated with annotations in file: "annotations_new.json"
       And I get item annotation collection
       And I change all image annotations label to "ball"
       When I update annotation collection
       Then Image annotations in host have label "ball"

    @testrail-C4523040
    @DAT-46436
    Scenario: Update - video
        Given Labels in file: "video_classes.json" are uploaded to test Dataset
        And Item in path "sample_video.mp4" is uploaded to "Dataset"
        And Item is annotated with annotations in file: "video_annotations.json"
        And I get item annotation collection
        And I change all annotations label to "ball"
        When I update annotation collection
        Then Annotations in host have label "ball"

    @testrail-C4523040
    @DAT-46436
    Scenario: Delete
        Given Classes in file: "classes_new.json" are uploaded to test Dataset
        And Item in path "assets_split/annotation_collection/0000000162.jpg" is uploaded to "Dataset"
        And Item is annotated with annotations in file: "assets_split/annotation_collection/annotations_new.json"
        And I get item annotation collection
        When I delete annotation collection
        Then Item in host has no annotations

    @testrail-C4523040
    @DAT-46436
    Scenario: Upload - image
        Given Classes in file: "assets_split/annotation_collection/classes_new.json" are uploaded to test Dataset
        And Item in path "assets_split/annotation_collection/0000000162.jpg" is uploaded to "Dataset"
        And I create item annotation collection
        And I add a few annotations to image
        When I upload annotation collection
        Then Annotations in host equal annotations uploaded

    @testrail-C4523040
    @DAT-46436
    Scenario: Upload - video
        Given Labels in file: "assets_split/annotation_collection/video_classes.json" are uploaded to test Dataset
        And Item in path "assets_split/annotation_collection/sample_video.mp4" is uploaded to "Dataset"
        And I create item annotation collection
        And I add a few annotations to video
        And I add a few frames to annotations
        When I upload annotation collection
        Then Annotations in host equal annotations uploaded

    @testrail-C4523040
    @DAT-46436
   Scenario: Upload annotation from_json - with UTF-8 character
       Given Classes in file: "annotation_collection/classes.json" are uploaded to test Dataset
       And Item in path "assets_split/annotation_collection/0000000162.jpg" is uploaded to "Dataset"
       And I get AnnotationCollection from json "annotation_collection/annotations_new.json"
       When I upload annotation collection
       Then Annotations in host equal annotations uploaded

