Feature: Upload annotation testing

    Background: Initiate Platform Interface
      Given Platform Interface is initialized as dlp and Environment is set according to git branch
      And I create a project by the name of "upload_annotations"
      And I create a dataset with a random name
      When I add "free_text" attribute to ontology
            | key=1 | title=attr1 | scope=all |
      When I add "free_text" attribute to ontology
          | key=2 | title=attr2 | scope=all |

    @testrail-C4523047
    @DAT-46449
    Scenario: Upload image annotations from file
          Given Classes in file: "assets_split/annotations_upload/classes_new.json" are uploaded to test Dataset
          And Item in path "assets_split/annotations_upload/0000000162.jpg" is uploaded to "Dataset"
          When Item is annotated with annotations in file: "assets_split/annotations_upload/annotations_new.json"
          Then Item annotations in host equal annotations in file "assets_split/annotations_upload/annotations_new.json"

    @testrail-C4523047
    @DAT-46449
    Scenario: Upload video annotations from file
          Given Classes in file: "assets_split/annotations_upload/video_classes.json" are uploaded to test Dataset
          And Item in path "assets_split/annotations_upload/sample_video.mp4" is uploaded to "Dataset"
          When Item is annotated with annotations in file: "assets_split/annotations_upload/video_annotations.json"
          Then Item video annotations in host equal annotations in file "assets_split/annotations_upload/video_annotations.json"

    @testrail-C4523047
    @DAT-46449
    Scenario: Upload audio annotations from file
          Given Classes in file: "classes_new.json" are uploaded to test Dataset
          And Item in path "simple_audio.mp3" is uploaded to "Dataset"
          When Item is annotated with annotations in file: "audio_annotations.json"
          Then audio in host has annotation added



