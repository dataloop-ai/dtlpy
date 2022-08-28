Feature: Upload annotation testing

    Background: Initiate Platform Interface
      Given Platform Interface is initialized as dlp and Environment is set according to git branch
      And There is a project by the name of "upload_annotations"
      And I create a dataset with a random name

    @testrail-C4523047
    Scenario: Upload image annotations from file
          Given Classes in file: "assets_split/annotations_upload/classes_new.json" are uploaded to test Dataset
          And Dataset ontology has attributes "attr1" and "attr2"
          And Item in path "assets_split/annotations_upload/0000000162.jpg" is uploaded to "Dataset"
          When Item is annotated with annotations in file: "assets_split/annotations_upload/annotations_new.json"
          Then Item annotations in host equal annotations in file "assets_split/annotations_upload/annotations_new.json"

    @testrail-C4523047
    Scenario: Upload video annotations from file
          Given Classes in file: "assets_split/annotations_upload/video_classes.json" are uploaded to test Dataset
          And Item in path "assets_split/annotations_upload/sample_video.mp4" is uploaded to "Dataset"
          When Item is annotated with annotations in file: "assets_split/annotations_upload/video_annotations.json"
          Then Item video annotations in host equal annotations in file "assets_split/annotations_upload/video_annotations.json"

    @testrail-C4523047
    Scenario: Upload audio annotations from file
          Given Classes in file: "classes_new.json" are uploaded to test Dataset
          And Item in path "simple_audio.mp3" is uploaded to "Dataset"
          When Item is annotated with annotations in file: "audio_annotations.json"
          Then audio in host has annotation added


